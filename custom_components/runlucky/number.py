"""Number platform (writable device parameters) for RunLucky."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._base import RunLuckyReadableEntity
from .const import DOMAIN, FLOW_RATE_UNIT, NUMBER_ENTITIES, WATER_VOLUME_UNIT
from .coordinator import RunLuckyCoordinator

_LOGGER = logging.getLogger(__name__)

_DYNAMIC_VOLUME_MAX = {0: 44, 1: 166.65, 2: 10}
_DYNAMIC_PRODUCTION_MAX = {0: 26420, 1: 99999, 2: 99.99}


class RunLuckyNumber(RunLuckyReadableEntity, NumberEntity):
    """A numeric setting written through ``control-device``."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
        description: dict[str, Any],
    ) -> None:
        """Initialise the number entity."""
        super().__init__(coordinator, device_id, key)
        self._description = description
        self._attr_native_min_value = description["min"]
        self._attr_native_max_value = description["max"]
        self._attr_native_step = description["step"]
        self._attr_native_unit_of_measurement = description.get("unit")
        self._attr_icon = description.get("icon", "mdi:tune-variant")

    @property
    def native_max_value(self) -> float:
        """Return a unit aware maximum, like the app does.

        The static limits come from the app's own validation, but a device may
        report a value above them (e.g. ``resinVolume`` 200 on a model where the
        app only allows 1-75 L), so the current value is always a valid maximum.
        """
        maximum = self._attr_native_max_value
        if self._description.get("unit_dynamic"):
            unit = self.protocol.get("waterVolumeUnit")
            if isinstance(unit, (int, float)):
                table = (
                    _DYNAMIC_PRODUCTION_MAX
                    if self._key == "periodicWaterProduction"
                    else _DYNAMIC_VOLUME_MAX
                )
                maximum = table.get(int(unit), maximum)
        current = self.protocol_value
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            maximum = max(maximum, float(current))
        return maximum

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit for dynamic-unit settings."""
        if not self._description.get("unit_dynamic"):
            return self._attr_native_unit_of_measurement
        unit = self.protocol.get("waterVolumeUnit")
        if isinstance(unit, (int, float)):
            table = (
                WATER_VOLUME_UNIT
                if self._key == "periodicWaterProduction"
                else FLOW_RATE_UNIT
            )
            return table.get(int(unit))
        return None

    @property
    def native_value(self) -> float | None:
        """Return the current setting."""
        value = self.protocol_value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Write the new setting to the device."""
        payload: Any = value
        if float(value).is_integer() and self._attr_native_step >= 1:
            payload = int(value)
        await self.coordinator.async_control(self._device_id, {self._key: payload})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunLucky number entities."""
    coordinator: RunLuckyCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[NumberEntity] = []
    for device in coordinator.devices.values():
        for key, description in NUMBER_ENTITIES.items():
            if not coordinator.model_supports(device, key):
                continue
            entities.append(
                RunLuckyNumber(coordinator, device.device_id, key, description)
            )
    async_add_entities(entities)
