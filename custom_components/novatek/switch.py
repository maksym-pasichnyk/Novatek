"""Switch entity for the Novatek integration — load relay control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, KEY_SYS_FLAG
from .coordinator import NovatekCoordinator
from . import NovatekConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NovatekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([NovatekRelaySwitch(entry.runtime_data, entry)])


class NovatekRelaySwitch(CoordinatorEntity[NovatekCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "relay"
    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(
        self,
        coordinator: NovatekCoordinator,
        entry: NovatekConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_relay"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            model=coordinator.model,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data[KEY_SYS_FLAG] & (1 << 4))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_ctrl(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_ctrl(False)
        await self.coordinator.async_request_refresh()
