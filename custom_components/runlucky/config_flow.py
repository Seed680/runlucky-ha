"""Config flow for the RunLucky (润莱智联) integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import RunLuckyApiError, RunLuckyAuthError, RunLuckyClient
from .const import CONF_SHOW_ALL, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RunLuckyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI setup of a RunLucky account."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Ask for the account credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            session = aiohttp_client.async_get_clientsession(self.hass)
            client = RunLuckyClient(session, username, password)
            try:
                await client.async_login()
                devices = await client.async_get_devices()
            except RunLuckyAuthError as err:
                _LOGGER.warning("RunLucky login failed: %s", err)
                errors["base"] = "invalid_auth"
            except RunLuckyApiError as err:
                _LOGGER.warning("RunLucky connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - defensive, config flow must not crash
                _LOGGER.exception("Unexpected error during RunLucky setup")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    await self.async_set_unique_id(username.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"RunLucky ({username})",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
                ),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD, autocomplete="current-password"
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"scope": "RunLucky"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> "RunLuckyOptionsFlow":
        """Return the options flow."""
        return RunLuckyOptionsFlow()


class RunLuckyOptionsFlow(OptionsFlow):
    """Options: polling interval and entity filtering."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        show_all = self.config_entry.options.get(CONF_SHOW_ALL, False)
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=3600,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(CONF_SHOW_ALL, default=show_all): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
