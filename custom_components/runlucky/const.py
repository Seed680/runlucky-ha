"""Constants and data dictionary for the RunLucky (润莱智联) integration.

The whole data dictionary below was reverse engineered from the official
Android app (com.runxin.runlucky) which is a WebView shell around the Vue
front-end served from http://app.admin-runxin.com.
"""

from __future__ import annotations

DOMAIN = "runlucky"
MANUFACTURER = "润莱 RunLucky"

# NOTE: the vendor only serves plain HTTP - there is no TLS listener on
# api.admin-runxin.com (443 is closed).  Credentials therefore travel in
# cleartext; this is documented in the README.
API_BASE = "http://api.admin-runxin.com"

TOKEN_PATH = "/connect/token"
SCOPE = "RunLuckyIot"
CLIENT_ID = "RunLuckyIot_App"

# ABP application services (see custom_components/runlucky/api.py)
API_DEVICE = "/api/run-lucky/device/app/device"
API_DEVICE_CONTROL = "/api/run-lucky/device/app/device-control"
API_DEVICE_LOOKUP = "/api/run-lucky/device/app/device-lookup"
API_FAMILY = "/api/run-lucky/device/app/family"
API_FAMILY_DEVICE = "/api/run-lucky/device/app/family-device"
API_PROFILE = "/api/basic-data/app/profile"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10

# ---------------------------------------------------------------------------
# Enumerations (values are what the device reports / accepts)
# ---------------------------------------------------------------------------

STATION = {
    0: "系统正在运行",
    1: "系统正在反洗",
    2: "系统正在吸盐",
    3: "系统正在补水",
    4: "系统正在正洗",
    5: "系统正在关闭",
    6: "系统正在溶盐",
    7: "系统正在暂停1",
    8: "系统正在暂停2",
    9: "排空",
    10: "循环",
}

RO_STATION = {
    0: "待机",
    1: "冲洗",
    2: "制水",
    3: "回流",
}

F104_STATION = {
    0: "开启",
    1: "关闭",
}

SYSTEM_CLOSE_REASON = {
    0: "正常无漏水",
    1: "在关闭位置",
    257: "由于长按向下键在关闭位置",
    513: "由于泄漏点有信号在关闭位置",
    769: "由于连续用水时间过长在关闭位置",
    1025: "由于流量过大在关闭位置",
}

DEVICE_TIME_SCHEME = {
    0: "12小时制",
    1: "24小时制",
}

# 0 = gal, 1 = L, 2 = m3
WATER_VOLUME_UNIT = {
    0: "gal",
    1: "L",
    2: "m³",
}

FLOW_RATE_UNIT = {
    0: "gpm",
    1: "Lpm",
    2: "m³/h",
}

ABSORB_SALT_MODE = {
    0: "逆吸",
    1: "顺吸",
}

OUT_RELAY_MODE = {
    0: "b-01",
    1: "b-02",
}

REGENERATION_PATTERN = {
    0: "流量型",
    1: "时间型",
}

WORK_PATTERN = {
    0: "流量延滞型顺流再生",
    1: "流量即时型顺流再生(A03)",
    2: "智能流量型顺流再生",
    3: "流量延滞型逆流再生",
    4: "流量即时型逆流再生",
    5: "智能流量型顺流再生(A-13)",
    6: "过滤型",
    7: "流量延滞型",
    8: "流量即时型",
    9: "流量比较型",
}

DEVICE_LANGUAGE = {
    0: "中文",
    1: "英文",
    2: "西班牙语",
    3: "法语",
    4: "俄罗斯语",
    5: "意大利语",
    6: "德语",
    7: "波兰语",
}

DEVICE_MODEL = {
    0: "F79",
    1: "F150",
    2: "F67N",
    3: "F67D",
    4: "F71D",
    5: "F63D",
    6: "F65D",
    7: "F68D",
    8: "F69D",
    9: "F79D",
    10: "F82D",
    11: "F67N-A",
    12: "F105",
    13: "F97",
    14: "F136",
    15: "F138",
    16: "F139",
    17: "F152",
    18: "C600A",
    19: "C800D",
    20: "F104HW",
    21: "F149",
    22: "F163",
    23: "F151",
}

WATER_IMMERSION_DETECTOR = {
    0: "水浸传感器未安装",
    1: "水浸传感器工作正常",
    2: "检测到漏水",
    3: "检测到漏水且传感器电量不足",
}

# Models that expose the RO (reverse osmosis) sub-system
RO_MODELS = {"C600A", "C800D"}
# Models that expose the F104 on/off state
F104_MODELS = {"F104HW"}
# Models with a pressure sensor
PRESSURE_MODELS = {"F149", "F163", "F151"}

# ---------------------------------------------------------------------------
# Read-side protocol fields -> entity descriptions
# ---------------------------------------------------------------------------
# key: protocolData key
# name: English friendly name (Chinese lives in translations)
# device_class / state_class / unit are filled in sensor.py

SENSOR_FIELDS: dict[str, dict] = {
    "flowRate": {
        "name": "Flow rate",
        "icon": "mdi:water-pump",
        "unit_from": "flowRateUnit",
    },
    "residualWaterProduction": {
        "name": "Residual water production",
        "icon": "mdi:water",
        "unit_from": "residualWaterProductionUnit",
        "device_class": "water",
        "state_class": "total",
    },
    "remainingDay": {
        "name": "Remaining days",
        "icon": "mdi:calendar-clock",
        "unit": "d",
    },
    "pressureValue": {
        "name": "Water pressure",
        "icon": "mdi:gauge",
        "unit": "MPa",
        "suggested_digits": 2,
    },
    "pressureSettingValue": {
        "name": "Pressure setpoint",
        "icon": "mdi:gauge",
        "unit": "MPa",
        "suggested_digits": 2,
    },
    "washCountdownTime": {
        "name": "Cycle countdown",
        "icon": "mdi:timer-sand",
        "unit": "s",
        "duration": True,
    },
    "pauseRemainingTime": {
        "name": "Pause remaining",
        "icon": "mdi:timer-pause",
        "unit": "s",
        "duration": True,
    },
    "saltDissolutionRemainingTime": {
        "name": "Brine dissolution remaining",
        "icon": "mdi:timer-sand",
        "unit": "s",
        "duration": True,
    },
    "absorbSaltTimeRemaining": {
        "name": "Brine draw remaining",
        "icon": "mdi:timer-sand",
        "unit": "s",
        "duration": True,
    },
    "backWashTimeRemaining": {
        "name": "Backwash remaining",
        "icon": "mdi:timer-sand",
        "unit": "s",
        "duration": True,
    },
    "saltTankRefillTimeRemaining": {
        "name": "Brine tank refill remaining",
        "icon": "mdi:timer-sand",
        "unit": "s",
        "duration": True,
    },
    "dailyWaterConsumption": {
        "name": "Water used today",
        "icon": "mdi:water-minus-outline",
        "unit_from": "dailyWaterConsumptionUnit",
        "device_class": "water",
        "state_class": "total_increasing",
    },
    "averageWeeklyWaterConsumption": {
        "name": "Average daily use (7 days)",
        "icon": "mdi:chart-bar",
        "unit_from": "averageWeeklyWaterConsumptionUnit",
        "device_class": "water",
        "state_class": "measurement",
    },
    "regenerationTimes": {
        "name": "Regenerations",
        "icon": "mdi:counter",
        "state_class": "total_increasing",
    },
    "inletTds": {
        "name": "Inlet TDS",
        "icon": "mdi:water-opacity",
        "unit": "ppm",
        "state_class": "measurement",
    },
    "outletTds": {
        "name": "Outlet TDS",
        "icon": "mdi:water-check-outline",
        "unit": "ppm",
        "state_class": "measurement",
    },
    "roFilterMaterialLifespanPercentage": {
        "name": "RO filter lifespan",
        "icon": "mdi:filter",
        "unit": "%",
        "state_class": "measurement",
    },
    "percentageOfLifespanOfPacCarbonFiberCompositeFilterMaterial": {
        "name": "PAC filter lifespan",
        "icon": "mdi:filter",
        "unit": "%",
        "state_class": "measurement",
    },
    "pacTotalWaterProductionTime": {
        "name": "PAC total production time",
        "icon": "mdi:timer-outline",
        "unit": "min",
        "state_class": "total_increasing",
    },
    "roTotalWaterProductionTime": {
        "name": "RO total production time",
        "icon": "mdi:timer-outline",
        "unit": "min",
        "state_class": "total_increasing",
    },
    "rawWaterHardness": {
        "name": "Raw water hardness",
        "icon": "mdi:water-percent",
        "unit": "mg/L",
        "state_class": "measurement",
    },
    "resinVolume": {
        "name": "Resin volume",
        "icon": "mdi:cube-outline",
        "unit": "L",
    },
}

ENUM_SENSORS: dict[str, dict] = {
    "station": {"name": "System status", "enum": STATION, "icon": "mdi:water-sync"},
    "f104Station": {"name": "Valve state", "enum": F104_STATION, "icon": "mdi:valve"},
    "roStation": {"name": "RO status", "enum": RO_STATION, "icon": "mdi:water-check"},
    "systemCloseReason": {
        "name": "Valve close reason",
        "enum": SYSTEM_CLOSE_REASON,
        "icon": "mdi:valve-closed",
    },
    "regenerationPattern": {
        "name": "Regeneration pattern",
        "enum": REGENERATION_PATTERN,
        "icon": "mdi:autorenew",
    },
    "workPattern": {"name": "Work pattern", "enum": WORK_PATTERN, "icon": "mdi:cog-sync"},
    "deviceModel": {"name": "Device model", "enum": DEVICE_MODEL, "icon": "mdi:chip"},
    "waterImmersionDetector1": {
        "name": "Leak sensor 1",
        "enum": WATER_IMMERSION_DETECTOR,
        "icon": "mdi:water-alert",
    },
    "waterImmersionDetector2": {
        "name": "Leak sensor 2",
        "enum": WATER_IMMERSION_DETECTOR,
        "icon": "mdi:water-alert",
    },
    "waterImmersionDetector3": {
        "name": "Leak sensor 3",
        "enum": WATER_IMMERSION_DETECTOR,
        "icon": "mdi:water-alert",
    },
    "waterImmersionDetector4": {
        "name": "Leak sensor 4",
        "enum": WATER_IMMERSION_DETECTOR,
        "icon": "mdi:water-alert",
    },
}

BINARY_SENSORS: dict[str, dict] = {
    "saltShortageReminder": {
        "name": "Salt shortage",
        "device_class": "problem",
        "icon": "mdi:shaker-outline",
    },
    "saltShortageAlarm": {
        "name": "Salt shortage alarm",
        "device_class": "problem",
        "icon": "mdi:shaker-alert-outline",
    },
    "resinReplacementReminder": {
        "name": "Resin replacement required",
        "device_class": "problem",
        "icon": "mdi:swap-horizontal",
    },
    "filterMaterialReminder": {
        "name": "Filter material replacement required",
        "device_class": "problem",
        "icon": "mdi:filter-remove",
    },
    "waterLeakage": {
        "name": "Water leakage",
        "device_class": "moisture",
        "icon": "mdi:water-alert",
    },
    "clockChipFault": {
        "name": "Clock chip fault",
        "device_class": "problem",
        "icon": "mdi:clock-alert",
    },
    "memoryErrorFault": {
        "name": "Memory error",
        "device_class": "problem",
        "icon": "mdi:memory",
    },
    "multiplePositionSignalFault": {
        "name": "Multiple position signal fault",
        "device_class": "problem",
        "icon": "mdi:alert-circle",
    },
    "noPositionSignalFault": {
        "name": "No position signal fault",
        "device_class": "problem",
        "icon": "mdi:alert-circle",
    },
    "isIntelligentInspection": {
        "name": "Intelligent inspection",
        "icon": "mdi:robot",
    },
    "vacationPattern": {
        "name": "Vacation mode",
        "icon": "mdi:airplane",
    },
}

# ---------------------------------------------------------------------------
# Write-side (POST control-device body keys)
# ---------------------------------------------------------------------------

NUMBER_ENTITIES: dict[str, dict] = {
    "rawWaterHardness": {
        "name": "Raw water hardness",
        "min": 50,
        "max": 1500,
        "step": 1,
        "unit": "mg/L",
    },
    "saltAddition": {
        "name": "Salt addition",
        "min": 0,
        "max": 100,
        "step": 0.1,
        "unit": "kg",
    },
    "periodicWaterProduction": {
        "name": "Capacity per cycle",
        "min": 0,
        "max": 9999,
        "step": 0.01,
        "unit_dynamic": True,
    },
    "continuousWaterTime": {
        "name": "Continuous water time",
        "min": 0,
        "max": 120,
        "step": 1,
        "unit": "min",
    },
    "flowRateOff": {
        "name": "Flow shut-off threshold",
        "min": 0,
        "max": 600,
        "step": 0.01,
        "unit_dynamic": True,
    },
    "backWashIntervalNumber": {
        "name": "Backwash interval",
        "min": 0,
        "max": 20,
        "step": 1,
    },
    "filterMaterialWorkingDay": {
        "name": "Filter material working days",
        "min": 10,
        "max": 600,
        "step": 1,
        "unit": "d",
    },
    "maximumRegenerationIntervalDay": {
        "name": "Max regeneration interval",
        "min": 0,
        "max": 40,
        "step": 1,
        "unit": "d",
    },
    "operationDay": {
        "name": "Operation days",
        "min": 0,
        "max": 99,
        "step": 1,
        "unit": "d",
    },
    "regenerationAlarmNumber": {
        "name": "Regeneration alarm count",
        "min": 5,
        "max": 1200,
        "step": 1,
    },
    "resinVolume": {
        "name": "Resin volume",
        "min": 1,
        "max": 75,
        "step": 1,
        "unit": "L",
    },
    "washingIncreaseNumber": {
        "name": "Wash frequency increase",
        "min": 0,
        "max": 20,
        "step": 1,
    },
}

SELECT_ENTITIES: dict[str, dict] = {
    "absorbSaltMode": {"name": "Brine draw mode", "enum": ABSORB_SALT_MODE},
    "deviceTimeScheme": {"name": "Clock format", "enum": DEVICE_TIME_SCHEME},
    "language": {"name": "Device language", "enum": DEVICE_LANGUAGE},
    "outRelayMode": {"name": "Output relay mode", "enum": OUT_RELAY_MODE},
    "waterVolumeUnit": {"name": "Water volume unit", "enum": WATER_VOLUME_UNIT},
    "workPattern": {"name": "Work pattern", "enum": WORK_PATTERN},
}

# Time-of-day style settings, written as "HH:MM:SS" (the API accepts "HH:MM"
# as well, but always reports HH:MM:SS).
_HMS = r"^([0-9]{1,3}:)?[0-5][0-9]:[0-5][0-9]$"

TEXT_ENTITIES: dict[str, dict] = {
    "washInitiationTime": {"name": "Regeneration start time", "pattern": r"^([0-2][0-9]:)?[0-5][0-9](:[0-5][0-9])?$"},
    "absorbSaltSlowWashTime": {"name": "Brine draw + slow rinse time", "pattern": _HMS},
    "backWashTime": {"name": "Backwash time", "pattern": _HMS},
    "saltTankRefillTime": {"name": "Brine tank refill time", "pattern": _HMS},
    "washTime": {"name": "Fast rinse time", "pattern": _HMS},
    "regeneratingTriggerTime": {"name": "Regeneration trigger time", "pattern": r"^([0-2][0-9]:)?[0-5][0-9](:[0-5][0-9])?$"},
}

# ---------------------------------------------------------------------------
# ABP error handling
# ---------------------------------------------------------------------------

AUTH_ERRORS = ("invalid_grant", "invalid_token", "unauthorized")
