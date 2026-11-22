"""Shared entity base classes for the RunLucky integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import RunLuckyCoordinator, RunLuckyDevice


class RunLuckyEntity(CoordinatorEntity[RunLuckyCoordinator]):
    """Base class for every RunLucky entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RunLuckyCoordinator,
        device_id: str,
        key: str,
    ) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_translation_key = key

    @property
    def device(self) -> RunLuckyDevice:
        """Return the runtime device record."""
        return self.coordinator.devices[self._device_id]

    @property
    def protocol(self) -> dict[str, Any]:
        """Return the current ``protocolData`` mapping."""
        return self.device.protocol or {}

    @property
    def available(self) -> bool:
        """Return True when the cloud returned data for this device."""
        return super().available and self.device.available

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device registry information."""
        return self.device.device_info()

    @property
    def unique_id(self) -> str:
        """Return a stable unique id."""
        return f"{self._device_id}_{self._key}"


class RunLuckyReadableEntity(RunLuckyEntity):
    """Base entity whose value lives in ``protocolData``."""

    @property
    def protocol_value(self) -> Any:
        """Return the raw protocol value."""
        return self.protocol.get(self._key)
