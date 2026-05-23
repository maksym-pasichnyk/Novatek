"""Constants for the Novatek integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "novatek"

DEFAULT_SCAN_INTERVAL: Final = 5
DEFAULT_TIMEOUT: Final = 10

KEY_VOLTAGE: Final = "voltage"
KEY_CURRENT: Final = "current"
KEY_FREQUENCY: Final = "frequency"
KEY_ACTIVE_POWER: Final = "active_power"
KEY_APPARENT_POWER: Final = "apparent_power"
KEY_ENERGY_TOTAL: Final = "energy_total"
KEY_APPARENT_ENERGY: Final = "apparent_energy"
KEY_TEMPERATURE: Final = "temperature"
KEY_ENERGY_DAILY: Final = "energy_daily"
KEY_ENERGY_WEEKLY: Final = "energy_weekly"
KEY_ENERGY_MONTHLY: Final = "energy_monthly"
KEY_SYS_FLAG: Final = "sys_flag"
KEY_FAUL_FLAG: Final = "faul_flag"
KEY_AR_TIME: Final = "ar_time"
