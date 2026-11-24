#!/usr/bin/env python3
"""Regenerate strings.json + translations from const.py.

The entity lists in ``custom_components/runlucky/const.py`` are the single
source of truth; this script mirrors them into the translation files, keeping
hand written Chinese names that are already present.

    python tools/gen_translations.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CMP = REPO / "custom_components" / "runlucky"
sys.path.insert(0, str(CMP))

import const  # noqa: E402

ZH = {
    # sensors
    "flowRate": "瞬时流量",
    "residualWaterProduction": "剩余产水量",
    "remainingDay": "剩余天数",
    "pressureValue": "水压",
    "pressureSettingValue": "压力设定值",
    "washCountdownTime": "周期倒计时",
    "pauseRemainingTime": "暂停剩余时间",
    "saltDissolutionRemainingTime": "溶盐剩余时间",
    "absorbSaltTimeRemaining": "吸盐剩余时间",
    "backWashTimeRemaining": "反洗剩余时间",
    "saltTankRefillTimeRemaining": "补盐箱剩余时间",
    "roFilterMaterialLifespanPercentage": "RO 滤芯寿命",
    "percentageOfLifespanOfPacCarbonFiberCompositeFilterMaterial": "PAC 复合滤料寿命",
    "pacTotalWaterProductionTime": "PAC 累计制水时间",
    "roTotalWaterProductionTime": "RO 累计制水时间",
    "rawWaterHardness": "原水硬度",
    "resinVolume": "树脂量",
    "dailyWaterConsumption": "今日用水量",
    "averageWeeklyWaterConsumption": "近7天日均用水量",
    "regenerationTimes": "再生次数",
    "inletTds": "进水 TDS",
    "outletTds": "出水 TDS",
    # enum sensors
    "station": "系统状态",
    "f104Station": "阀门状态",
    "roStation": "RO 状态",
    "systemCloseReason": "关阀原因",
    "regenerationPattern": "再生类型",
    "workPattern": "工作模式",
    "deviceModel": "设备型号",
    "waterImmersionDetector1": "漏水检测 1",
    "waterImmersionDetector2": "漏水检测 2",
    "waterImmersionDetector3": "漏水检测 3",
    "waterImmersionDetector4": "漏水检测 4",
    "waterImmersionDetector5": "漏水检测 5",
    # binary sensors
    "saltShortageReminder": "缺盐提醒",
    "saltShortageAlarm": "缺盐报警",
    "resinReplacementReminder": "需更换树脂",
    "filterMaterialReminder": "需更换滤料",
    "waterLeakage": "漏水",
    "clockChipFault": "时钟芯片故障",
    "memoryErrorFault": "存储故障",
    "multiplePositionSignalFault": "多工位信号故障",
    "noPositionSignalFault": "无工位信号故障",
    "isIntelligentInspection": "智能巡检",
    "vacationPattern": "度假模式状态",
    # numbers
    "saltAddition": "加盐量",
    "periodicWaterProduction": "周期产水量",
    "continuousWaterTime": "连续用水时间",
    "flowRateOff": "流量关阀阈值",
    "backWashIntervalNumber": "反洗间隔次数",
    "filterMaterialWorkingDay": "滤料工作天数",
    "maximumRegenerationIntervalDay": "最大再生间隔天数",
    "operationDay": "运行天数",
    "regenerationAlarmNumber": "再生报警次数",
    "washingIncreaseNumber": "冲洗次数增加",
    # selects
    "absorbSaltMode": "吸盐方式",
    "deviceTimeScheme": "时钟制式",
    "language": "设备语言",
    "outRelayMode": "输出继电器模式",
    "waterVolumeUnit": "水量单位",
    # text
    "washInitiationTime": "再生启动时间",
    "absorbSaltSlowWashTime": "吸盐慢洗时间",
    "backWashTime": "反洗时间",
    "saltTankRefillTime": "盐箱补水时间",
    "washTime": "正洗时间",
    "regeneratingTriggerTime": "再生触发时间",
    # buttons / switch
    "forced_regeneration": "立即再生",
    "ro_forced_regeneration": "RO 强制冲洗",
    "enter_vacation": "进入度假模式",
    "exit_vacation": "退出度假模式",
    "sync_clock": "同步设备时钟",
    "query_device": "从设备读取数据",
    "vacation_mode": "度假模式",
}

# keys whose English name differs from the const "name" field
EN = {
    "forced_regeneration": "Start regeneration",
    "ro_forced_regeneration": "Start RO flush",
    "enter_vacation": "Enter vacation mode",
    "exit_vacation": "Exit vacation mode",
    "sync_clock": "Sync device clock",
    "query_device": "Read from device",
    "vacation_mode": "Vacation mode",
}

CONFIG = {
    "config": {
        "step": {
            "user": {
                "title": "RunLucky account",
                "description": "Sign in with the account you use in the "
                "润莱智联 (RunLucky) app. The vendor cloud only speaks "
                "plain HTTP, so your password leaves this device unencrypted.",
                "data": {"username": "Email or phone", "password": "Password"},
            }
        },
        "error": {
            "invalid_auth": "Wrong email/phone or password.",
            "cannot_connect": "Could not reach the RunLucky cloud.",
            "no_devices": "No water softener is bound to this account.",
            "unknown": "Unexpected error, check the logs.",
        },
        "abort": {"already_configured": "This account is already configured."},
    },
    "options": {
        "step": {
            "init": {
                "title": "RunLucky options",
                "data": {
                    "scan_interval": "Polling interval",
                    "show_all_entities": "Show unused / unsupported entities",
                },
                "data_description": {
                    "scan_interval": "How often the cloud cache is polled.",
                    "show_all_entities": "Also create RO, PAC, TDS, pressure and "
                    "uninstalled leak-sensor entities that this device model "
                    "reports but cannot use.",
                },
            }
        }
    },
}

CONFIG_ZH = {
    "config": {
        "step": {
            "user": {
                "title": "润莱账号",
                "description": "请使用「润莱智联」App 的账号登录。"
                "厂商服务器仅提供 HTTP 明文接口，密码将以明文传输。",
                "data": {"username": "邮箱或手机号", "password": "密码"},
            }
        },
        "error": {
            "invalid_auth": "账号或密码错误。",
            "cannot_connect": "无法连接润莱云服务。",
            "no_devices": "该账号下没有绑定软水机。",
            "unknown": "未知错误，请查看日志。",
        },
        "abort": {"already_configured": "该账号已配置。"},
    },
    "options": {
        "step": {
            "init": {
                "title": "润莱选项",
                "data": {
                    "scan_interval": "轮询间隔",
                    "show_all_entities": "显示本机用不到 / 未安装的实体",
                },
                "data_description": {
                    "scan_interval": "云端缓存数据的拉取间隔。",
                    "show_all_entities": "同时创建该型号用不到的 RO、PAC、TDS、"
                    "压力以及未安装的水浸传感器实体。",
                },
            }
        }
    },
}


def main() -> int:
    platforms: dict[str, dict[str, str]] = {
        "sensor": {},
        "binary_sensor": {},
        "button": {},
        "switch": {"vacation_mode": EN["vacation_mode"]},
        "number": {},
        "select": {},
        "text": {},
    }
    for key, desc in const.SENSOR_FIELDS.items():
        platforms["sensor"][key] = desc["name"]
    for key, desc in const.ENUM_SENSORS.items():
        platforms["sensor"][key] = desc["name"]
    for key, desc in const.BINARY_SENSORS.items():
        platforms["binary_sensor"][key] = desc["name"]
    for key, desc in const.NUMBER_ENTITIES.items():
        platforms["number"][key] = desc["name"]
    for key, desc in const.SELECT_ENTITIES.items():
        platforms["select"][key] = desc["name"]
    for key, desc in const.TEXT_ENTITIES.items():
        platforms["text"][key] = desc["name"]
    from_buttons = [
        "forced_regeneration",
        "ro_forced_regeneration",
        "enter_vacation",
        "exit_vacation",
        "sync_clock",
        "query_device",
    ]
    for key in from_buttons:
        platforms["button"][key] = EN[key]

    missing_zh = []

    def build(lang: dict[str, str] | None, config: dict) -> dict:
        entity = {}
        for platform, keys in platforms.items():
            entity[platform] = {}
            for key, en_name in keys.items():
                if lang is None:
                    name = en_name
                else:
                    name = lang.get(key) or ""
                    if not name:
                        missing_zh.append(f"{platform}.{key}")
                        name = en_name
                entity[platform][key] = {"name": name}
        return {"entity": entity, **config}

    strings = build(None, CONFIG)
    en = build(None, CONFIG)
    zh = build(ZH, CONFIG_ZH)

    (CMP / "strings.json").write_text(
        json.dumps(strings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (CMP / "translations").mkdir(exist_ok=True)
    (CMP / "translations" / "en.json").write_text(
        json.dumps(en, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (CMP / "translations" / "zh-Hans.json").write_text(
        json.dumps(zh, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    counts = {p: len(k) for p, k in platforms.items()}
    print("entities per platform:", counts)
    print("total:", sum(counts.values()))
    if missing_zh:
        print("!! missing Chinese names:", missing_zh)
        return 1
    print("translations written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
