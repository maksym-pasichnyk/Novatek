"""The Novatek integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NovatekAuthError, NovatekClient, NovatekConnectionError
from .coordinator import NovatekCoordinator

type NovatekConfigEntry = ConfigEntry[NovatekCoordinator]

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: NovatekConfigEntry) -> bool:
    """Set up Novatek from a config entry."""
    session = async_get_clientsession(hass)
    client = NovatekClient(session, host=entry.data[CONF_HOST], password=entry.data[CONF_PASSWORD])
    try:
        await client.async_authenticate()
    except NovatekAuthError as err:
        raise ConfigEntryAuthFailed(err) from err
    except NovatekConnectionError as err:
        raise ConfigEntryNotReady(err) from err
    
    coordinator = NovatekCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NovatekConfigEntry) -> bool:
    """Unload a config entry."""
    await entry.runtime_data.client.async_logout()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
