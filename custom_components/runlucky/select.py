"""Select platform (enumerated device settings) for RunLucky."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyReadableEntity
from .const import DOMAIN, SELECT_ENTITIES
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)


class RunLuckySelect(RunLuckyReadableEntity, SelectEntity):
    """A setting with a fixed set of values."""

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the select entity."""
        super().__init__(coordinator, device_id, key)
        self._enum: dict[Any, str] = description["enum"]
        self._label_to_value = {label: value for value, label in self._enum.items()}
        self._attr_icon = description.get("icon", "mdi:format-list-bulleted")
        self._attr_options = list(self._label_to_value)

    @property
    def current_option(self) -> str | None:
        """Return the current label."""
        return self._enum.get(self.protocol_value)

    async def async_select_option(self, option: str) -> None:
        """Write the new option."""
        value = self._label_to_value.get(option)
        if value is None:
            raise ValueError(f"unsupported option {option}")
        await self.coordinator.async_control(self._device_id, {self._key: value})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky selects."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SelectEntity] = []
    for device in coordinator.devices.values():
        for key, description in SELECT_ENTITIES.items():
            if key == "workPattern" and str(device.protocol.get("regenerationPattern")) == "0":
                # flow based models read workPattern but do not accept a write
                pass
            if not coordinator.model_supports(device, key):
                continue
            entities.append(
                RunLuckySelect(coordinator, device.device_id, key, description)
            )
    async_add_entities(entities)
