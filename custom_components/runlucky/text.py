"""Text platform for time-of-day style settings (HH:MM:SS)."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyReadableEntity
from .const import DOMAIN, TEXT_ENTITIES
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)


class RunLuckyTimeText(RunLuckyReadableEntity, TextEntity):
    """A ``HH:MM:SS`` value stored as text."""

    _attr_mode = TextMode.TEXT

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the text entity."""
        super().__init__(coordinator, device_id, key)
        self._pattern = description["pattern"]
        self._attr_icon = "mdi:timer-outline"
        self._attr_native_min = 4
        self._attr_native_max = 8
        self._attr_pattern = self._pattern

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        value = self.protocol_value
        return str(value) if value not in (None, "") else None

    async def async_set_value(self, value: str) -> None:
        """Write a new value."""
        value = value.strip()
        if not re.match(self._pattern, value):
            raise ValueError(f"value {value!r} does not match {self._pattern}")
        parts = value.split(":")
        if len(parts) == 2:
            value = f"{value}:00"
        await self.coordinator.async_control(self._device_id, {self._key: value})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky text entities."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[TextEntity] = []
    for device in coordinator.devices.values():
        for key, description in TEXT_ENTITIES.items():
            if not coordinator.model_supports(device, key):
                continue
            entities.append(
                RunLuckyTimeText(coordinator, device.device_id, key, description)
            )
    async_add_entities(entities)
