"""HTTP client for the Novatek EM-125 / 126 / 129 family.

Authentication is a challenge–response:

    GET /api/login?device_info  ->  {"STATUS": "OK", "device_id": <int>}
    GET /api/login?salt         ->  {"STATUS": "OK", "SALT": "<hex>"}
    hash = SHA1(model + password + salt)
    GET /api/login?login=<hash> ->  {"STATUS": "OK", "SID": "<sid>"}

All subsequent requests: /<SID>/api/all/get?<key>  ->  scaled integer.

    volt_msr    / 10    -> V
    cur_msr     / 100   -> A
    freq_msr    / 100   -> Hz
    powa_msr    / 1     -> W
    pows_msr    / 1     -> VA
    enrga_msr   / 1     -> Wh   (total active energy)
    enrgs_msr   / 1     -> VAh  (total apparent energy)
    enrga_d_msr / 1     -> Wh   (daily active energy)
    enrga_w_msr / 1     -> Wh   (weekly active energy)
    enrga_m_msr / 1     -> Wh   (monthly active energy)
    tempr_msr   / 10    -> °C   (EM-126T / EM-126TS only)
    sys_flag            -> bitmask — device state flags
    faul_flag           -> bitmask — fault/protection flags
    ar_time             -> seconds remaining until auto-reconnect (APV)
"""

from __future__ import annotations

import asyncio
import hashlib

import aiohttp
from aiohttp import ClientError, ClientTimeout

from .const import (
    DEFAULT_TIMEOUT,
    KEY_ACTIVE_POWER,
    KEY_APPARENT_ENERGY,
    KEY_APPARENT_POWER,
    KEY_AR_TIME,
    KEY_CURRENT,
    KEY_ENERGY_DAILY,
    KEY_ENERGY_MONTHLY,
    KEY_ENERGY_TOTAL,
    KEY_ENERGY_WEEKLY,
    KEY_FAUL_FLAG,
    KEY_FREQUENCY,
    KEY_SYS_FLAG,
    KEY_TEMPERATURE,
    KEY_VOLTAGE,
)

DEVICE_MODELS: dict[int, str] = {
    243: "EM-125",
    255: "EM-125S",
    271: "EM-129",
    285: "EM-126TS",
    293: "EM-126T",
}

# Models that have a built-in temperature sensor (DS18B20)
TEMPERATURE_MODELS: frozenset[str] = frozenset({"EM-126T", "EM-126TS"})

MEASUREMENTS: tuple[tuple[str, str, float], ...] = (
    ("volt_msr",    KEY_VOLTAGE,          10.0),
    ("cur_msr",     KEY_CURRENT,         100.0),
    ("freq_msr",    KEY_FREQUENCY,       100.0),
    ("powa_msr",    KEY_ACTIVE_POWER,      1.0),
    ("pows_msr",    KEY_APPARENT_POWER,    1.0),
    ("enrga_msr",   KEY_ENERGY_TOTAL,      1.0),
    ("enrgs_msr",   KEY_APPARENT_ENERGY,   1.0),
    ("enrga_d_msr", KEY_ENERGY_DAILY,      1.0),
    ("enrga_w_msr", KEY_ENERGY_WEEKLY,     1.0),
    ("enrga_m_msr", KEY_ENERGY_MONTHLY,    1.0),
)

# sys_flag bitmask: bit index -> short key used in HA entity IDs
SYS_FLAG_BITS: dict[int, str] = {
    0:  "apv_voltage",      # APV countdown by voltage
    1:  "apv_current",      # APV countdown by current
    2:  "apv_power",        # APV countdown by power
    3:  "apv_delay",        # turn-on delay countdown
    4:  "relay_on",         # load relay state (on = energised)
    6:  "event_control",    # load controlled by schedule
    7:  "manual_control",   # load controlled manually by user
    8:  "vacation_lock",    # load blocked by vacation mode
    9:  "ntp_synced",       # time synchronised with NTP server
    10: "cloud_synced",     # time synchronised with cloud
    11: "panel_locked",     # front panel locked
    12: "apv_frequency",    # APV countdown by frequency
    16: "wifi_client",      # WiFi in station/client mode
    17: "wifi_connected",   # WiFi connected and IP obtained
    18: "wifi_ap",          # WiFi in access-point mode
    19: "wifi_ap_active",   # WiFi AP running and IP issued
    26: "web_running",      # WEB service active
    27: "cloud_running",    # CLOUD service active
    28: "ntp_running",      # NTP service active
    29: "dns_running",      # DNS service active
}

# faul_flag bitmask: bit index -> short key
FAUL_FLAG_BITS: dict[int, str] = {
    0:  "overvoltage",          # upper voltage threshold exceeded
    1:  "undervoltage",         # lower voltage threshold exceeded
    2:  "voltage_290v",         # voltage > 290 V detected
    3:  "voltage_apv_limit",    # voltage APV reconnect limit exceeded
    4:  "overcurrent",          # current threshold exceeded
    5:  "current_17a",          # current > 17 A detected
    6:  "current_apv_limit",    # current APV reconnect limit exceeded
    7:  "overpower",            # power threshold exceeded
    8:  "power_apv_limit",      # power APV reconnect limit exceeded
    9:  "temp_sensor_fault",    # temperature sensor fault
    10: "temp_sensor_open",     # temperature sensor open circuit
    11: "temp_sensor_short",    # temperature sensor short circuit
    12: "rtc_fault",            # RTC clock failure
    13: "relay_fault",          # relay fault (current detected when relay off)
    14: "time_limit_blocked",   # blocked by operating time limit
    15: "overfrequency",        # upper frequency threshold exceeded
    16: "underfrequency",       # lower frequency threshold exceeded
    17: "frequency_apv_limit",  # frequency APV reconnect limit exceeded
    30: "not_calibrated",       # device not calibrated
    31: "settings_damaged",     # settings memory corrupted
}


class NovatekConnectionError(Exception):
    """Device is unreachable or returned a non-success status."""


class NovatekAuthError(Exception):
    """Authentication failed — bad password or unsupported device."""


class NovatekSessionExpiredError(Exception):
    """Session token expired — device requires re-authentication."""


class NovatekClient:
    """Async client for Novatek-Electro EM-125/126/129 power meters."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        password: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session
        self._host = host
        self._password = password
        self._timeout = ClientTimeout(total=timeout)
        self._mac: str | None = None
        self._sid: str | None = None
        self._model: str | None = None

    @property
    def mac(self) -> str:
        """Return the device's MAC address (available after authentication)."""
        if self._mac is None:
            raise RuntimeError("MAC address not available before authentication")
        return self._mac

    @property
    def model(self) -> str:
        """Return the detected device model (available after authentication)."""
        if self._model is None:
            raise RuntimeError("Model not available before authentication")
        return self._model

    @property
    def has_temperature(self) -> bool:
        """Return True if the device has a built-in temperature sensor."""
        return self._model in TEMPERATURE_MODELS
    
    async def async_get_data(self) -> dict[str, float | int]:
        try:
            return await self._fetch_data()
        except NovatekSessionExpiredError:
            await self.async_authenticate()
            return await self._fetch_data()
    
    async def _fetch_data(self) -> dict[str, float | int]:
        data: dict[str, float | int] = {}
        for api_key, canonical_key, divisor in MEASUREMENTS:
            raw = await self._get_measurement(api_key)
            data[canonical_key] = raw / divisor

        if self.has_temperature:
            raw = await self._get_measurement("tempr_msr")
            data[KEY_TEMPERATURE] = raw / 10.0

        data[KEY_SYS_FLAG] = await self._get_measurement("sys_flag")
        data[KEY_FAUL_FLAG] = await self._get_measurement("faul_flag")
        data[KEY_AR_TIME] = await self._get_measurement("ar_time")

        return data

    async def async_authenticate(self) -> None:
        r = await self._raw_get("/api/login?device_info")
        device_id = r["device_id"]
        model = DEVICE_MODELS.get(device_id)
        if model is None:
            raise NovatekAuthError(f"Unsupported device_id {device_id!r}")

        r = await self._raw_get("/api/login?salt")
        sha_1 = hashlib.sha1(f"{model}{self._password}{r["SALT"]}".encode("utf-8"))

        r = await self._raw_get(f"/api/login?login={sha_1.hexdigest()}")
        sid = r["SID"]

        r = await self._raw_get(f"/{sid}/api/all/get?device_mac")
        mac = r["device_mac"][4:]

        self._sid = sid
        self._mac = mac
        self._model = model

    async def async_ctrl(self, on: bool) -> None:
        """Turn the load relay on (True) or off (False)."""
        cmd = "on" if on else "off"
        await self._raw_get(f"/{self._sid}/api/utils/ctrl?{cmd}")

    async def async_reset_energy(self) -> None:
        """Reset all energy counters on the device."""
        await self._raw_get(f"/{self._sid}/api/utils/enrgrst")

    async def async_reboot(self) -> None:
        """Reboot the device."""
        await self._raw_get(f"/{self._sid}/api/utils/reboot")

    async def async_logout(self) -> None:
        """Terminate the session on the device."""
        try:
            await self._raw_get(f"/api/login?logout={self._sid}")
        except (NovatekAuthError, NovatekSessionExpiredError, NovatekConnectionError):
            pass

    async def _get_measurement(self, key: str) -> int:
        r = await self._raw_get(f"/{self._sid}/api/all/get?{key}")
        return int(r[key])

    async def _raw_get(self, path: str) -> dict[str, object]:
        url = f"http://{self._host}{path}"
        try:
            async with self._session.get(url, timeout=self._timeout, allow_redirects=False) as resp:
                if resp.status == 302:
                    raise NovatekSessionExpiredError("Session expired")
                data = await resp.json(content_type=None)
        except (ClientError, asyncio.TimeoutError, ValueError, KeyError) as err:
            raise NovatekConnectionError(str(err)) from err

        match data["STATUS"]:
            case "OK":
                return data
            case "ERROR_LOGIN":
                raise NovatekAuthError(f"Login failed: {data!r}")
            case "ERROR_LOGOUT":
                raise NovatekConnectionError(f"Logout failed: {data!r}")
            case status:
                raise NovatekConnectionError(f"Device returned {status!r}: {data!r}")
