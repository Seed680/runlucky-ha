"""Entity level tests for the RunLucky integration (no HA runtime needed).

Runs against a real Home Assistant installation on sys.path, but with a stub
coordinator so no cloud access is required.

    HA_SRC=<path to homeassistant wheel unpacked> python tests/test_entities.py
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
HA_SRC = os.environ.get("HA_SRC")
if HA_SRC:
    sys.path.insert(0, HA_SRC)
sys.path.insert(0, str(REPO))

from custom_components.runlucky import const  # noqa: E402
from custom_components.runlucky.binary_sensor import RunLuckyBinarySensor  # noqa: E402
from custom_components.runlucky.button import BUTTONS, RunLuckyButton  # noqa: E402
from custom_components.runlucky.coordinator import RunLuckyDevice  # noqa: E402
from custom_components.runlucky.number import RunLuckyNumber  # noqa: E402
from custom_components.runlucky.select import RunLuckySelect  # noqa: E402
from custom_components.runlucky.sensor import (  # noqa: E402
    RunLuckyEnumSensor,
    RunLuckyFieldSensor,
)
from custom_components.runlucky.switch import RunLuckyVacationSwitch  # noqa: E402
from custom_components.runlucky.text import RunLuckyTimeText  # noqa: E402

PROTOCOL = {
    # representative protocolData captured from a real softener
    # (device id / mac removed, non sensitive model values kept)
    "deviceModel": 1,
    "language": 0,
    "deviceTimeScheme": 1,
    "currentTime": "22:57:00",
    "washInitiationTime": "00:00:00",
    "continuousWaterTime": 60,
    "flowRateOff": 2.5,
    "waterVolumeUnit": 2,
    "workPattern": 7,
    "regeneratingTriggerTime": "00:00:00",
    "flowRate": 0,
    "systemCloseReason": 0,
    "backWashTime": "00:07:00",
    "backWashTimeRemaining": "00:09:00",
    "absorbSaltSlowWashTime": "00:58:00",
    "absorbSaltTimeRemaining": "00:09:00",
    "saltTankRefillTime": "00:26:30",
    "saltTankRefillTimeRemaining": "00:08:58",
    "washTime": "00:09:00",
    "washCountdownTime": "00:09:00",
    "maximumRegenerationIntervalDay": 30,
    "resinVolume": 200,
    "clockChipFault": False,
    "saltShortageAlarm": False,
    "saltShortageReminder": False,
    "station": 1,
    "residualWaterProduction": 3.63,
    "residualWaterProductionUnit": 2,
    "dailyWaterConsumption": 0.02,
    "dailyWaterConsumptionUnit": 2,
    "averageWeeklyWaterConsumption": 0.03,
    "averageWeeklyWaterConsumptionUnit": 2,
    "periodicWaterProduction": 0.01,
    "periodicWaterProductionUnit": 2,
    "saltAddition": 0,
    "remainingDay": 0,
    "regenerationPattern": 0,
    "rawWaterHardness": 220,
    "absorbSaltMode": 0,
    "vacationPattern": False,
    "saltDissolutionRemainingTime": 0,
    "pauseRemainingTime": 0,
    "regenerationTimes": 7,
    "pressureValue": 0,
    "roStation": 2,
    "inletTds": 180,
    "outletTds": 12,
    "waterLeakage": False,
    "roFilterMaterialLifespanPercentage": 87.654,
    "percentageOfLifespanOfPacCarbonFiberCompositeFilterMaterial": 55,
    "waterImmersionDetector1": 2,
}

FAILURES = 0


def check(name: str, cond: bool, extra: object = "") -> None:
    global FAILURES
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES += 1
        print(f"  FAIL {name} {extra}")


class StubClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    async def async_control(self, device_id, payload):
        self.calls.append(("control", device_id, payload))

    async def async_forced_regeneration(self, device_id):
        self.calls.append(("forced_regeneration", device_id))

    async def async_enter_vacation(self, device_id):
        self.calls.append(("enter_vacation", device_id))

    async def async_exit_vacation(self, device_id):
        self.calls.append(("exit_vacation", device_id))

    async def async_sync_clock(self, device_id, time_str):
        self.calls.append(("sync_clock", device_id, time_str))

    async def async_query_device(self, device_id):
        self.calls.append(("query_device", device_id))


class StubCoordinator:
    """Mimics the bits of RunLuckyCoordinator the entities touch."""

    def __init__(self, device: RunLuckyDevice) -> None:
        self.devices = {device.device_id: device}
        self.client = StubClient()
        self.last_update_success = True
        self.refreshes = 0

    async def async_request_refresh(self) -> None:
        self.refreshes += 1

    async def async_control(self, device_id, payload):
        await self.client.async_control(device_id, payload)
        self.refreshes += 1

    def model_supports(self, device, key):  # noqa: D102
        return True


def translations() -> dict:
    return json.loads(
        (REPO / "custom_components/runlucky/strings.json").read_text(encoding="utf-8")
    )


async def main() -> int:
    device = RunLuckyDevice({"deviceId": "dev-1", "deviceName": "软水机", "mac": "AA:BB"})
    device.update({"protocolData": PROTOCOL})
    coordinator = StubCoordinator(device)

    print("device")
    check("name", device.name == "软水机")
    check("model name", device.model_name == "F150", device.model_name)
    check("device_info identifiers", device.device_info()["identifiers"] == {("runlucky", "dev-1")})
    check("available", device.available)

    print("field sensors")
    water = RunLuckyFieldSensor(coordinator, "dev-1", "residualWaterProduction",
                                const.SENSOR_FIELDS["residualWaterProduction"])
    check("residual value", water.native_value == 3.63, water.native_value)
    check("residual unit m3", water.native_unit_of_measurement == "m³",
          water.native_unit_of_measurement)
    flow = RunLuckyFieldSensor(coordinator, "dev-1", "flowRate", const.SENSOR_FIELDS["flowRate"])
    check("flow unit m3/h", flow.native_unit_of_measurement == "m³/h",
          flow.native_unit_of_measurement)
    check("flow value", flow.native_value == 0, flow.native_value)
    pct = RunLuckyFieldSensor(
        coordinator, "dev-1", "roFilterMaterialLifespanPercentage",
        const.SENSOR_FIELDS["roFilterMaterialLifespanPercentage"])
    check("percentage rounded", pct.native_value == 87.7, pct.native_value)
    press = RunLuckyFieldSensor(coordinator, "dev-1", "pressureValue",
                                const.SENSOR_FIELDS["pressureValue"])
    check("pressure unit", press.native_unit_of_measurement == "MPa")
    daily = RunLuckyFieldSensor(coordinator, "dev-1", "dailyWaterConsumption",
                                const.SENSOR_FIELDS["dailyWaterConsumption"])
    check("daily use unit", daily.native_unit_of_measurement == "m³",
          daily.native_unit_of_measurement)
    check("daily use value", daily.native_value == 0.02, daily.native_value)
    weekly = RunLuckyFieldSensor(coordinator, "dev-1", "averageWeeklyWaterConsumption",
                                 const.SENSOR_FIELDS["averageWeeklyWaterConsumption"])
    check("weekly unit", weekly.native_unit_of_measurement == "m³")
    tds = RunLuckyFieldSensor(coordinator, "dev-1", "inletTds",
                              const.SENSOR_FIELDS["inletTds"])
    check("inlet tds", tds.native_value == 180 and tds.native_unit_of_measurement == "ppm")
    backwash = RunLuckyFieldSensor(coordinator, "dev-1", "backWashTimeRemaining",
                                   const.SENSOR_FIELDS["backWashTimeRemaining"])
    check("duration seconds", backwash.native_value == 540, backwash.native_value)
    check("duration unit", backwash.native_unit_of_measurement == "s")
    check("duration device class", str(backwash.device_class).endswith("duration"),
          backwash.device_class)
    pause = RunLuckyFieldSensor(coordinator, "dev-1", "pauseRemainingTime",
                                const.SENSOR_FIELDS["pauseRemainingTime"])
    check("numeric duration", pause.native_value == 0, pause.native_value)
    regen_count = RunLuckyFieldSensor(coordinator, "dev-1", "regenerationTimes",
                                      const.SENSOR_FIELDS["regenerationTimes"])
    check("regeneration count", regen_count.native_value == 7)
    resin = RunLuckyNumber(coordinator, "dev-1", "resinVolume",
                           const.NUMBER_ENTITIES["resinVolume"])
    check("resin value above app max", resin.native_value == 200.0, resin.native_value)
    check("resin max relaxed", resin.native_max_value == 200.0, resin.native_max_value)
    check("translation key", water.translation_key == "residualWaterProduction")
    check("unique id", water.unique_id == "dev-1_residualWaterProduction")

    print("enum sensors")
    station = RunLuckyEnumSensor(coordinator, "dev-1", "station", const.ENUM_SENSORS["station"])
    check("station label", station.native_value == "系统正在反洗", station.native_value)
    check("station options", "系统正在反洗" in station.options)
    ro = RunLuckyEnumSensor(coordinator, "dev-1", "roStation", const.ENUM_SENSORS["roStation"])
    check("ro label", ro.native_value == "制水", ro.native_value)

    print("binary sensors")
    salt = RunLuckyBinarySensor(coordinator, "dev-1", "saltShortageReminder",
                                const.BINARY_SENSORS["saltShortageReminder"])
    check("salt reminder off", salt.is_on is False)
    alarm = RunLuckyBinarySensor(coordinator, "dev-1", "saltShortageAlarm",
                                 const.BINARY_SENSORS["saltShortageAlarm"])
    check("salt alarm off", alarm.is_on is False)
    resin = RunLuckyBinarySensor(coordinator, "dev-1", "resinReplacementReminder",
                                 const.BINARY_SENSORS["resinReplacementReminder"])
    check("resin ok off", resin.is_on is False)
    check("salt device class", salt.device_class is not None)

    print("numbers")
    hardness = RunLuckyNumber(coordinator, "dev-1", "rawWaterHardness",
                              const.NUMBER_ENTITIES["rawWaterHardness"])
    check("hardness unit", hardness.native_unit_of_measurement == "mg/L")
    check("hardness max", hardness.native_max_value == 1500)
    check("hardness value live", hardness.native_value == 220.0)
    production = RunLuckyNumber(coordinator, "dev-1", "periodicWaterProduction",
                                const.NUMBER_ENTITIES["periodicWaterProduction"])
    check("production max for m3", production.native_max_value == 99.99,
          production.native_max_value)
    check("production unit m3", production.native_unit_of_measurement == "m³",
          production.native_unit_of_measurement)
    await hardness.async_set_native_value(320)
    check("control payload", coordinator.client.calls[-1] == ("control", "dev-1",
          {"rawWaterHardness": 320}), coordinator.client.calls[-1])

    print("selects")
    salt_mode = RunLuckySelect(coordinator, "dev-1", "absorbSaltMode",
                               const.SELECT_ENTITIES["absorbSaltMode"])
    check("select current", salt_mode.current_option == "逆吸", salt_mode.current_option)
    check("select options", set(salt_mode.options) == {"逆吸", "顺吸"})
    await salt_mode.async_select_option("顺吸")
    check("select write", coordinator.client.calls[-1] == ("control", "dev-1",
          {"absorbSaltMode": 1}), coordinator.client.calls[-1])

    print("text")
    rinse = RunLuckyTimeText(coordinator, "dev-1", "washInitiationTime",
                             const.TEXT_ENTITIES["washInitiationTime"])
    check("text value", rinse.native_value == "00:00:00", rinse.native_value)
    await rinse.async_set_value("11:15:00")
    check("text write", coordinator.client.calls[-1] == ("control", "dev-1",
          {"washInitiationTime": "11:15:00"}), coordinator.client.calls[-1])
    trigger = RunLuckyTimeText(coordinator, "dev-1", "regeneratingTriggerTime",
                               const.TEXT_ENTITIES["regeneratingTriggerTime"])
    check("trigger value", trigger.native_value == "00:00:00", trigger.native_value)
    await trigger.async_set_value("23:30:00")
    check("trigger write", coordinator.client.calls[-1] == ("control", "dev-1",
          {"regeneratingTriggerTime": "23:30:00"}), coordinator.client.calls[-1])
    try:
        await rinse.async_set_value("nonsense")
        check("text rejects invalid", False)
    except ValueError:
        check("text rejects invalid", True)

    print("switch")
    vacation = RunLuckyVacationSwitch(coordinator, "dev-1")
    check("vacation off", vacation.is_on is False)
    await vacation.async_turn_on()
    check("vacation enter", ("enter_vacation", "dev-1") in coordinator.client.calls)
    await vacation.async_turn_off()
    check("vacation exit", ("exit_vacation", "dev-1") in coordinator.client.calls)

    print("buttons")
    regen = RunLuckyButton(coordinator, "dev-1", "forced_regeneration", "mdi:autorenew",
                           "forced_regeneration")
    await regen.async_press()
    check("regen pressed", ("forced_regeneration", "dev-1") in coordinator.client.calls)
    for key, icon, action in BUTTONS:
        check(f"button {key} has translation",
              key in translations()["entity"]["button"], key)
    check("refresh requested", coordinator.refreshes > 0)

    print("translations coverage")
    doc = translations()
    missing = []
    for platform, keys in (
        ("sensor", list(const.SENSOR_FIELDS) + list(const.ENUM_SENSORS)),
        ("binary_sensor", list(const.BINARY_SENSORS)),
        ("number", list(const.NUMBER_ENTITIES)),
        ("select", list(const.SELECT_ENTITIES)),
        ("text", list(const.TEXT_ENTITIES)),
        ("switch", ["vacation_mode"]),
        ("button", [k for k, _, _ in BUTTONS] + ["ro_forced_regeneration"]),
    ):
        for key in keys:
            if key not in doc["entity"][platform]:
                missing.append(f"{platform}.{key}")
    check("all translation keys present", not missing, missing)

    zh = json.loads(
        (REPO / "custom_components/runlucky/translations/zh-Hans.json").read_text(
            encoding="utf-8"
        )
    )
    zh_missing = [
        k
        for k in doc["entity"]["sensor"]
        if zh["entity"]["sensor"][k]["name"] == doc["entity"]["sensor"][k]["name"]
    ]
    check("zh-Hans sensor names localised", not zh_missing, zh_missing)

    print()
    print("ALL TESTS PASSED" if FAILURES == 0 else f"{FAILURES} FAILURE(S)")
    return 0 if FAILURES == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
