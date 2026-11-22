"""Sensor platform for the RunLucky integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyReadableEntity
from .const import (
    DOMAIN,
    ENUM_SENSORS,
    FLOW_RATE_UNIT,
    SENSOR_FIELDS,
    WATER_VOLUME_UNIT,
)
from .coordinator import RunLuckyCoordinator

PERCENTAGE_KEYS = (
    "roFilterMaterialLifespanPercentage",
    "percentageOfLifespanOfPacCarbonFiberCompositeFilterMaterial",
)


def _volume_unit(value: Any) -> str | None:
    """Map the numeric water volume unit to its label."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return WATER_VOLUME_UNIT.get(int(value))
    return None


def _flow_unit(value: Any) -> str | None:
    """Map the numeric water volume unit to the matching flow unit."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return FLOW_RATE_UNIT.get(int(value))
    return None


def _as_seconds(value: Any) -> int | None:
    """Convert ``HH:MM:SS`` / ``MM:SS`` / plain seconds to seconds."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split(":")
    if not all(part.isdigit() for part in parts):
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


class RunLuckyFieldSensor(RunLuckyReadableEntity, SensorEntity):
    """Numeric / textual sensor backed by a single protocolData key."""

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, device_id, key)
        self._description = description
        self._attr_icon = description.get("icon")
        if device_class := description.get("device_class"):
            self._attr_device_class = SensorDeviceClass(device_class)
        if state_class := description.get("state_class"):
            self._attr_state_class = SensorStateClass(state_class)
        self._attr_native_unit_of_measurement = description.get("unit")
        if description.get("duration") and not description.get("device_class"):
            self._attr_device_class = SensorDeviceClass.DURATION
        if (digits := description.get("suggested_digits")) is not None:
            self._attr_suggested_display_precision = digits

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit, honouring the unit configured on the device."""
        if self._key == "flowRate":
            return _flow_unit(self.protocol.get("waterVolumeUnit"))
        if unit_from := self._description.get("unit_from"):
            return _volume_unit(self.protocol.get(unit_from)) or _volume_unit(
                self.protocol.get("waterVolumeUnit")
            )
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        value = self.protocol_value
        if isinstance(value, bool):
            return int(value)
        if self._description.get("duration"):
            return _as_seconds(value)
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            if self._key in PERCENTAGE_KEYS:
                return round(float(value), 1)
            return value
        return None


class RunLuckyEnumSensor(RunLuckyReadableEntity, SensorEntity):
    """Sensor translating a numeric enum into a human readable label."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the enum sensor."""
        super().__init__(coordinator, device_id, key)
        self._enum: dict[Any, str] = description["enum"]
        self._attr_icon = description.get("icon")
        self._attr_options = list(dict.fromkeys(self._enum.values()))

    @property
    def native_value(self) -> str | None:
        """Return the translated enum label."""
        return self._enum.get(self.protocol_value)



def _present(device: Any, key: str) -> bool:
    """Return True when the device actually reports this protocol key.

    Models differ a lot (RO sub-system, leak detectors, pressure sensor ...),
    and the cloud simply omits the keys a model does not have, so entity
    creation follows the reported protocol instead of hardcoded model lists.
    """
    protocol = getattr(device, "protocol", None) or {}
    return key in protocol


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky sensors."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = []

    for device in coordinator.devices.values():
        for key, description in SENSOR_FIELDS.items():
            if not _present(device, key):
                continue
            entities.append(
                RunLuckyFieldSensor(coordinator, device.device_id, key, description)
            )
        for key, description in ENUM_SENSORS.items():
            if not _present(device, key):
                continue
            entities.append(
                RunLuckyEnumSensor(coordinator, device.device_id, key, description)
            )

    async_add_entities(entities)
