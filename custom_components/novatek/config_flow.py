"""Config flow for the Novatek integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac

from .api import NovatekAuthError, NovatekClient, NovatekConnectionError
from .const import DOMAIN

if TYPE_CHECKING:
    from . import NovatekConfigEntry

PASSWORD_ONLY_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})
USER_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PASSWORD): str,
})


class NovatekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Novatek."""

    VERSION = 1
    _discovered_host: str

    async def _async_setup_entry(self, host: str, password: str) -> ConfigFlowResult:
        """Connect, deduplicate by MAC, and create the config entry."""
        client = NovatekClient(async_get_clientsession(self.hass), host=host, password=password)
        await client.async_authenticate()
        mac = format_mac(client.mac)
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        return self.async_create_entry(title=f"{client.model} ({mac.upper()})", data={CONF_HOST: host, CONF_PASSWORD: password})

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle manual entry by IP address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self._async_setup_entry(user_input[CONF_HOST], user_input[CONF_PASSWORD])
            except NovatekAuthError:
                errors["base"] = "invalid_auth"
            except NovatekConnectionError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> ConfigFlowResult:
        """Handle DHCP discovery."""
        mac = format_mac(discovery_info.macaddress)
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})

        self._discovered_host = discovery_info.ip
        self.context["title_placeholders"] = {"hostname": f"{discovery_info.hostname.upper()} ({mac.upper()})"}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Ask for password after DHCP discovery."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self._async_setup_entry(self._discovered_host, user_input[CONF_PASSWORD])
            except NovatekAuthError:
                errors["base"] = "invalid_auth"
            except NovatekConnectionError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=PASSWORD_ONLY_SCHEMA,
            errors=errors,
            description_placeholders=self.context.get("title_placeholders", {}),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication after ConfigEntryAuthFailed."""
        entry: NovatekConfigEntry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                client = NovatekClient(
                    async_get_clientsession(self.hass),
                    host=entry.data[CONF_HOST],
                    password=user_input[CONF_PASSWORD],
                )
                await client.async_authenticate()
            except NovatekAuthError:
                errors["base"] = "invalid_auth"
            except NovatekConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=PASSWORD_ONLY_SCHEMA,
            errors=errors,
        )
