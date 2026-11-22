"""Set up the RunLucky (润莱智联) integration."""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .api import RunLuckyApiError, RunLuckyAuthError, RunLuckyClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "sensor",
    "binary_sensor",
    "button",
    "switch",
    "number",
    "select",
    "text",
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RunLucky from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    client = RunLuckyClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await client.async_login()
    except RunLuckyAuthError as err:
        raise ConfigEntryAuthFailed(f"Login failed: {err}") from err
    except (RunLuckyApiError, aiohttp.ClientError) as err:
        raise ConfigEntryNotReady(f"Cannot reach RunLucky cloud: {err}") from err

    try:
        devices = await client.async_get_devices()
    except RunLuckyAuthError as err:
        raise ConfigEntryAuthFailed(f"Login failed: {err}") from err
    except RunLuckyApiError as err:
        raise ConfigEntryNotReady(f"Cannot list devices: {err}") from err

    if not devices:
        raise ConfigEntryNotReady(
            "No water softener is bound to this account (check the RunLucky app)"
        )

    scan_interval = max(
        int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        MIN_SCAN_INTERVAL,
    )
    coordinator = RunLuckyCoordinator(hass, client, devices, scan_interval)

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_load_model_settings()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
