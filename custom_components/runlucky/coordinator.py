"""Data update coordinator for the RunLucky integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RunLuckyApiError, RunLuckyAuthError, RunLuckyClient
from .const import DEFAULT_SCAN_INTERVAL, DEVICE_MODEL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class RunLuckyDevice:
    """Runtime information about a single water softener."""

    def __init__(self, entry: dict[str, Any]) -> None:
        """Initialise from the cloud device record."""
        self.device_id: str = str(entry.get("deviceId") or entry.get("id"))
        self.name: str = (
            entry.get("deviceName")
            or entry.get("name")
            or entry.get("mac")
            or f"RunLucky {self.device_id[-6:]}"
        )
        self.mac: str | None = entry.get("mac")
        self.serial: str | None = entry.get("deviceSerialNumber") or entry.get(
            "valveSerialNumber"
        )
        self.family_id = entry.get("familyId")
        self.family_name = entry.get("familyName")
        self.supports_flow_statistics: bool = bool(entry.get("isEnableFlowStatistics"))
        self.raw: dict[str, Any] = dict(entry)
        self.protocol: dict[str, Any] = {}
        self.model_name: str | None = None
        self.model_setting: dict[str, Any] = {}
        self.available = False

    @property
    def model_code(self) -> int | None:
        """Return the numeric device model."""
        value = self.protocol.get("deviceModel")
        return value if isinstance(value, int) else None

    def update(self, payload: dict[str, Any]) -> None:
        """Merge a fresh ``get-device-with--data`` payload."""
        protocol = payload.get("protocolData")
        if isinstance(protocol, dict):
            self.protocol = protocol
            self.available = True
        merged = dict(self.raw)
        merged.update({k: v for k, v in payload.items() if k != "protocolData"})
        self.raw = merged
        # the device list record is thin; the detail payload carries mac/serial
        self.mac = merged.get("mac") or self.mac
        self.serial = (
            merged.get("serialNumber")
            or merged.get("deviceSerialNumber")
            or merged.get("valveSerialNumber")
            or self.serial
        )
        if not payload.get("protocolData"):
            # some models never return protocolData when offline
            self.available = bool(payload)

        model = self.protocol.get("deviceModel")
        if isinstance(model, int):
            self.model_name = DEVICE_MODEL.get(model, str(model))

    def device_info(self) -> dict[str, Any]:
        """Return the Home Assistant device registry payload."""
        from .const import MANUFACTURER

        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, self.device_id)},
            "manufacturer": MANUFACTURER,
            "name": self.name,
            "model": self.model_name or self.raw.get("deviceModelName") or "Water softener",
            "sw_version": self.raw.get("firmwareVersion")
            or self.raw.get("version")
            or self.raw.get("softwareVersion"),
        }
        if self.serial:
            info["serial_number"] = str(self.serial)
        return info


class RunLuckyCoordinator(DataUpdateCoordinator[dict[str, RunLuckyDevice]]):
    """Poll every device of one account."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: RunLuckyClient,
        devices: list[dict[str, Any]],
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} devices",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.devices: dict[str, RunLuckyDevice] = {
            device.device_id: device for device in (RunLuckyDevice(d) for d in devices)
        }

    async def _async_update_data(self) -> dict[str, RunLuckyDevice]:
        """Fetch the current state of every device."""
        if not self.devices:
            raise UpdateFailed("no devices bound to this account")

        errors: list[str] = []
        for device in self.devices.values():
            try:
                payload = await self.client.async_get_device_data(device.device_id)
            except RunLuckyAuthError as err:
                raise UpdateFailed(f"authentication failed: {err}") from err
            except RunLuckyApiError as err:
                _LOGGER.debug("Update of %s failed: %s", device.name, err)
                device.available = False
                errors.append(f"{device.name}: {err}")
                continue
            device.update(payload or {})

        if errors and not any(d.available for d in self.devices.values()):
            raise UpdateFailed("; ".join(errors))
        return self.devices

    async def async_load_model_settings(self) -> None:
        """Fetch per-model setting capabilities (best effort)."""
        for device in self.devices.values():
            try:
                device.model_setting = await self.client.async_get_model_setting(
                    device.device_id,
                    device.protocol.get("deviceModel"),
                    device.protocol.get("regenerationPattern"),
                ) or {}
            except RunLuckyApiError as err:
                _LOGGER.debug("%s: model setting unavailable (%s)", device.name, err)

    async def async_control(self, device_id: str, payload: dict[str, Any]) -> None:
        """Write parameters and refresh afterwards."""
        await self.client.async_control(device_id, payload)
        await self.async_request_refresh()

    def model_supports(self, device: RunLuckyDevice, key: str) -> bool:
        """Return True when the model settings report the key as writable."""
        setting = device.model_setting
        if not isinstance(setting, dict) or not setting:
            return True
        for candidate in (
            key,
            key[0].lower() + key[1:],
            key[0].upper() + key[1:],
        ):
            if candidate in setting:
                value = setting[candidate]
                if isinstance(value, bool):
                    return value
                if isinstance(value, dict) and "isSupport" in value:
                    return bool(value["isSupport"])
                return True
        return False
