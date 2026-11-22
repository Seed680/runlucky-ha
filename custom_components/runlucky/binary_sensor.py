"""Binary sensor platform for the RunLucky integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyReadableEntity
from .const import BINARY_SENSORS, DOMAIN
from .coordinator import RunLuckyCoordinator


class RunLuckyBinarySensor(RunLuckyReadableEntity, BinarySensorEntity):
    """A boolean protocol field."""

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, device_id, key)
        self._attr_icon = description.get("icon")
        if device_class := description.get("device_class"):
            self._attr_device_class = BinarySensorDeviceClass(device_class)

    @property
    def is_on(self) -> bool:
        """Return the boolean state."""
        value = self.protocol_value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "on", "yes")
        return bool(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky binary sensors."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[BinarySensorEntity] = []
    for device in coordinator.devices.values():
        protocol = device.protocol or {}
        for key, description in BINARY_SENSORS.items():
            if key not in protocol:
                continue
            entities.append(
                RunLuckyBinarySensor(coordinator, device.device_id, key, description)
            )
    async_add_entities(entities)
