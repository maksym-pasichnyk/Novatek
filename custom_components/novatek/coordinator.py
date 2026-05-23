"""Coordinator for the Novatek integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NovatekAuthError, NovatekClient, NovatekConnectionError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NovatekCoordinator(DataUpdateCoordinator[dict[str, float | int]]):
    """Poll a Novatek device at a fixed interval."""

    def __init__(self, hass: HomeAssistant, client: NovatekClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    @property
    def model(self) -> str:
        """Return the detected device model."""
        return self.client.model

    @property
    def has_temperature(self) -> bool:
        """Return True if the device has a temperature sensor."""
        return self.client.has_temperature

    async def _async_update_data(self) -> dict[str, float | int]:
        try:
            return await self.client.async_get_data()
        except NovatekAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except NovatekConnectionError as err:
            raise UpdateFailed(f"Error communicating with Novatek device: {err}") from err