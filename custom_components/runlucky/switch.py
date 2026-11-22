"""Switch platform for the RunLucky integration."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyEntity
from .const import DOMAIN
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)


class RunLuckyVacationSwitch(RunLuckyEntity, SwitchEntity):
    """Vacation (away) mode of the softener."""

    _attr_icon = "mdi:airplane"

    def __init__(self, coordinator: RunLuckyCoordinator, device_id: str) -> None:
        """Initialise the switch."""
        super().__init__(coordinator, device_id, "vacation_mode")

    @property
    def is_on(self) -> bool:
        """Return True when the device is in vacation mode."""
        value = self.protocol.get("vacationPattern")
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Enter vacation mode."""
        await self.coordinator.client.async_enter_vacation(self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Leave vacation mode."""
        await self.coordinator.client.async_exit_vacation(self._device_id)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky switches."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        RunLuckyVacationSwitch(coordinator, device.device_id)
        for device in coordinator.devices.values()
    )
