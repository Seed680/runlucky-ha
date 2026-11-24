"""Button platform for the RunLucky integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyEntity
from .const import DOMAIN, RO_MODELS
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)

# (translation key, icon, action)
BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("forced_regeneration", "mdi:autorenew", "forced_regeneration"),
    ("enter_vacation", "mdi:airplane-takeoff", "enter_vacation"),
    ("exit_vacation", "mdi:airplane-landing", "exit_vacation"),
    ("sync_clock", "mdi:clock-check", "sync_clock"),
    ("query_device", "mdi:cloud-download", "query_device"),
)


class RunLuckyButton(RunLuckyEntity, ButtonEntity):
    """Generic cloud action button."""

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        icon: str,
        action: str,
    ) -> None:
        """Initialise the button."""
        super().__init__(coordinator, device_id, key)
        self._attr_icon = icon
        self._action = action

    async def async_press(self) -> None:
        """Run the action."""
        client = self.coordinator.client
        if self._action == "forced_regeneration":
            await client.async_forced_regeneration(self._device_id)
        elif self._action == "ro_forced_regeneration":
            await client.async_ro_forced_regeneration(self._device_id)
        elif self._action == "enter_vacation":
            await client.async_enter_vacation(self._device_id)
        elif self._action == "exit_vacation":
            await client.async_exit_vacation(self._device_id)
        elif self._action == "sync_clock":
            await client.async_sync_clock(
                self._device_id, datetime.now().strftime("%H:%M:%S")
            )
        elif self._action == "query_device":
            await client.async_query_device(self._device_id)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky buttons."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[ButtonEntity] = []
    for device in coordinator.devices.values():
        for key, icon, action in BUTTONS:
            entities.append(
                RunLuckyButton(coordinator, device.device_id, key, icon, action)
            )
        # the RO sub-system only exists on C600A / C800D (see const.RO_MODELS)
        if coordinator.entity_supported(
            device, "roStation", {"models": RO_MODELS}
        ):
            entities.append(
                RunLuckyButton(
                    coordinator,
                    device.device_id,
                    "ro_forced_regeneration",
                    "mdi:water-sync",
                    "ro_forced_regeneration",
                )
            )
    async_add_entities(entities)
