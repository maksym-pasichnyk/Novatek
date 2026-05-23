"""Binary sensor entities for the Novatek integration.

Each binary sensor maps a single bit from either the sys_flag or faul_flag
register. The bit position and register source are encoded in the description
key using the format  "<register>_bit<N>"  (e.g. "sys_flag_bit4").
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, KEY_FAUL_FLAG, KEY_SYS_FLAG
from .coordinator import NovatekCoordinator
from . import NovatekConfigEntry


@dataclass(frozen=True, kw_only=True)
class NovatekBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Extends the standard description with the register key and bit index."""

    register_key: str  # KEY_SYS_FLAG or KEY_FAUL_FLAG
    bit: int           # bit position (0 = LSB)


# ---------------------------------------------------------------------------
# sys_flag — device state bits
# ---------------------------------------------------------------------------
SYS_FLAG_DESCRIPTIONS: tuple[NovatekBinarySensorEntityDescription, ...] = (
    NovatekBinarySensorEntityDescription(
        key="sys_relay_on",
        translation_key="relay_on",
        device_class=BinarySensorDeviceClass.POWER,
        register_key=KEY_SYS_FLAG,
        bit=4,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_apv_voltage",
        translation_key="apv_voltage",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=0,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_apv_current",
        translation_key="apv_current",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=1,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_apv_power",
        translation_key="apv_power",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=2,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_apv_frequency",
        translation_key="apv_frequency",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=12,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_manual_control",
        translation_key="manual_control",
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=7,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_event_control",
        translation_key="event_control",
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=6,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_vacation_lock",
        translation_key="vacation_lock",
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=8,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_panel_locked",
        translation_key="panel_locked",
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=11,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_ntp_synced",
        translation_key="ntp_synced",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=9,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_wifi_connected",
        translation_key="wifi_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=17,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_cloud_running",
        translation_key="cloud_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=27,
    ),
    NovatekBinarySensorEntityDescription(
        key="sys_ntp_running",
        translation_key="ntp_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_SYS_FLAG,
        bit=28,
    ),
)

# ---------------------------------------------------------------------------
# faul_flag — protection / fault bits
# ---------------------------------------------------------------------------
FAUL_FLAG_DESCRIPTIONS: tuple[NovatekBinarySensorEntityDescription, ...] = (
    NovatekBinarySensorEntityDescription(
        key="faul_overvoltage",
        translation_key="overvoltage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=0,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_undervoltage",
        translation_key="undervoltage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=1,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_voltage_290v",
        translation_key="voltage_290v",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=2,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_voltage_apv_limit",
        translation_key="voltage_apv_limit",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=3,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_overcurrent",
        translation_key="overcurrent",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=4,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_current_17a",
        translation_key="current_17a",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=5,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_current_apv_limit",
        translation_key="current_apv_limit",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=6,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_overpower",
        translation_key="overpower",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=7,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_power_apv_limit",
        translation_key="power_apv_limit",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=8,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_temp_sensor_fault",
        translation_key="temp_sensor_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=9,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_temp_sensor_open",
        translation_key="temp_sensor_open",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=10,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_temp_sensor_short",
        translation_key="temp_sensor_short",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=11,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_rtc_fault",
        translation_key="rtc_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=12,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_relay_fault",
        translation_key="relay_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=13,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_time_limit_blocked",
        translation_key="time_limit_blocked",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=14,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_overfrequency",
        translation_key="overfrequency",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=15,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_underfrequency",
        translation_key="underfrequency",
        device_class=BinarySensorDeviceClass.PROBLEM,
        register_key=KEY_FAUL_FLAG,
        bit=16,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_frequency_apv_limit",
        translation_key="frequency_apv_limit",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=17,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_not_calibrated",
        translation_key="not_calibrated",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=30,
    ),
    NovatekBinarySensorEntityDescription(
        key="faul_settings_damaged",
        translation_key="settings_damaged",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_key=KEY_FAUL_FLAG,
        bit=31,
    ),
)

ALL_DESCRIPTIONS: tuple[NovatekBinarySensorEntityDescription, ...] = (
    *SYS_FLAG_DESCRIPTIONS,
    *FAUL_FLAG_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NovatekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        NovatekBinarySensor(coordinator, entry, desc) for desc in ALL_DESCRIPTIONS
    )


class NovatekBinarySensor(CoordinatorEntity[NovatekCoordinator], BinarySensorEntity):
    """A binary sensor derived from a single bit of a Novatek register."""

    _attr_has_entity_name = True
    entity_description: NovatekBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: NovatekCoordinator,
        entry: NovatekConfigEntry,
        description: NovatekBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            model=coordinator.model,
        )

    @property
    def is_on(self) -> bool:
        """Return True when the corresponding bit is set."""
        return bool(self.coordinator.data[self.entity_description.register_key] & (1 << self.entity_description.bit))
