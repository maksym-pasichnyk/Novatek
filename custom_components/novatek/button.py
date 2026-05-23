"""Button entities for the Novatek integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import NovatekClient
from .const import DOMAIN
from .coordinator import NovatekCoordinator
from . import NovatekConfigEntry


@dataclass(frozen=True, kw_only=True)
class NovatekButtonEntityDescription(ButtonEntityDescription):
    action: Callable[[NovatekClient], Coroutine[Any, Any, None]]


BUTTON_DESCRIPTIONS: tuple[NovatekButtonEntityDescription, ...] = (
    NovatekButtonEntityDescription(
        key="reset_energy",
        translation_key="reset_energy",
        entity_category=EntityCategory.CONFIG,
        action=lambda client: client.async_reset_energy(),
    ),
    NovatekButtonEntityDescription(
        key="reboot",
        translation_key="reboot",
        entity_category=EntityCategory.CONFIG,
        action=lambda client: client.async_reboot(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NovatekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        NovatekButton(coordinator, entry, desc) for desc in BUTTON_DESCRIPTIONS
    )


class NovatekButton(CoordinatorEntity[NovatekCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    entity_description: NovatekButtonEntityDescription

    def __init__(
        self,
        coordinator: NovatekCoordinator,
        entry: NovatekConfigEntry,
        description: NovatekButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            model=coordinator.model,
        )

    async def async_press(self) -> None:
        await self.entity_description.action(self.coordinator.client)
