"""Live end-to-end check: build every entity from real cloud data.

Needs a real Home Assistant install on sys.path (export HA_SRC).

    RUNLUCKY_USER=... RUNLUCKY_PASS=... HA_SRC=<ha src> python tools/probe_entities.py
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

import aiohttp

REPO = pathlib.Path(__file__).resolve().parent.parent
if ha_src := os.environ.get("HA_SRC"):
    sys.path.insert(0, ha_src)
sys.path.insert(0, str(REPO))

from custom_components.runlucky import const  # noqa: E402
from custom_components.runlucky.api import RunLuckyClient  # noqa: E402
from custom_components.runlucky.binary_sensor import (  # noqa: E402
    RunLuckyBinarySensor,
)
from custom_components.runlucky.button import BUTTONS, RunLuckyButton  # noqa: E402
from custom_components.runlucky.coordinator import (
    RunLuckyCoordinator,
    RunLuckyDevice,
)  # noqa: E402
from custom_components.runlucky.number import RunLuckyNumber  # noqa: E402
from custom_components.runlucky.select import RunLuckySelect  # noqa: E402
from custom_components.runlucky.sensor import (  # noqa: E402
    RunLuckyEnumSensor,
    RunLuckyFieldSensor,
)
from custom_components.runlucky.switch import RunLuckyVacationSwitch  # noqa: E402
from custom_components.runlucky.text import RunLuckyTimeText  # noqa: E402


class Stub:
    """Stand-in for RunLuckyCoordinator."""

    def __init__(self, client, devices, show_all=False):
        self.client = client
        self.show_all = show_all
        self.devices = {d.device_id: d for d in devices}
        self.last_update_success = True

    async def async_request_refresh(self):
        return None

    async def async_control(self, device_id, payload):
        print(f"    -> POST control {payload}")
        return await self.client.async_control(device_id, payload)

    def model_supports(self, device, key):
        # reuse the real implementation so the probe matches the integration
        return RunLuckyCoordinator.model_supports(self, device, key)

    def entity_supported(self, device, key, description=None):
        return RunLuckyCoordinator.entity_supported(self, device, key, description)


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = RunLuckyClient(
            session, os.environ["RUNLUCKY_USER"], os.environ["RUNLUCKY_PASS"]
        )
        await client.async_login()
        raw_devices = await client.async_get_devices()
        devices = []
        for raw in raw_devices:
            device = RunLuckyDevice(raw)
            data = await client.async_get_device_data(device.device_id)
            device.update(data)
            device.model_setting = (
                await client.async_get_model_setting(
                    device.device_id,
                    device.protocol.get("deviceModel"),
                    device.protocol.get("regenerationPattern"),
                )
                or {}
            )
            devices.append(device)

        stub = Stub(client, devices)

        for device in devices:
            print(f"\n=== {device.name} ({device.model_name}) {device.device_id}")
            missing = [
                key
                for key in list(const.SENSOR_FIELDS)
                + list(const.ENUM_SENSORS)
                + list(const.BINARY_SENSORS)
                + list(const.NUMBER_ENTITIES)
                + list(const.SELECT_ENTITIES)
                + list(const.TEXT_ENTITIES)
                if key not in device.protocol
            ]
            print(f"  protocol keys: {len(device.protocol)}, missing models keys: {missing}")

            print("  sensors:")
            hidden = []
            for key, desc in const.SENSOR_FIELDS.items():
                if not stub.entity_supported(device, key, desc):
                    hidden.append(key)
                    continue
                e = RunLuckyFieldSensor(stub, device.device_id, key, desc)
                unit = e.native_unit_of_measurement or ""
                print(f"    {key:60} {str(e.native_value):>10} {unit}")
            for key, desc in const.ENUM_SENSORS.items():
                if not stub.entity_supported(device, key, desc):
                    hidden.append(key)
                    continue
                e = RunLuckyEnumSensor(stub, device.device_id, key, desc)
                print(f"    {key:60} {str(e.native_value):>10}")
            if hidden:
                print(f"  filtered out (not supported by {device.model_name}): {hidden}")

            print("  binary sensors:")
            for key, desc in const.BINARY_SENSORS.items():
                if not stub.entity_supported(device, key, desc):
                    continue
                e = RunLuckyBinarySensor(stub, device.device_id, key, desc)
                print(f"    {key:60} {str(e.is_on):>10}")

            print("  writable:")
            for key, desc in const.NUMBER_ENTITIES.items():
                if not stub.model_supports(device, key):
                    continue
                e = RunLuckyNumber(stub, device.device_id, key, desc)
                print(
                    f"    number {key:40} {e.native_value} "
                    f"({e.native_min_value}..{e.native_max_value}) "
                    f"{e.native_unit_of_measurement or ''}"
                )
            for key, desc in const.SELECT_ENTITIES.items():
                if not stub.model_supports(device, key):
                    continue
                e = RunLuckySelect(stub, device.device_id, key, desc)
                print(f"    select {key:40} {e.current_option} of {e.options}")
            for key, desc in const.TEXT_ENTITIES.items():
                if not stub.model_supports(device, key):
                    continue
                e = RunLuckyTimeText(stub, device.device_id, key, desc)
                print(f"    text   {key:40} {e.native_value}")
            if stub.model_supports(device, "vacationPattern"):
                sw = RunLuckyVacationSwitch(stub, device.device_id)
                print(f"    switch vacation_mode                {sw.is_on}")
            for key, _, _ in BUTTONS:
                RunLuckyButton(stub, device.device_id, key, "mdi:x", key)
            print(f"    buttons: {[b[0] for b in BUTTONS]}")

        print("\nlive write test (sync clock):")
        first = devices[0]
        from datetime import datetime

        stamp = datetime.now().strftime("%H:%M:%S")
        await client.async_sync_clock(first.device_id, stamp)
        print(f"  currentTime={stamp} accepted")
        data = await client.async_get_device_data(first.device_id)
        print("  device reports currentTime =", data["protocolData"].get("currentTime"))


asyncio.run(main())
