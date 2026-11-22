"""Ad-hoc live probe: model setting variants + live query. Not part of the integration."""

import asyncio
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import importlib.util
import types

import aiohttp

PKG_DIR = REPO / "custom_components" / "runlucky"
pkg = types.ModuleType("probe")
pkg.__path__ = [str(PKG_DIR)]
sys.modules["probe"] = pkg


def load(name):
    spec = importlib.util.spec_from_file_location(f"probe.{name}", PKG_DIR / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


load("const")
api = load("api")

# device id from your own account: RUNLUCKY_DEVICE=<uuid> (see `runlucky_cli.py devices`)
DEVICE = os.environ.get("RUNLUCKY_DEVICE", "").strip()


async def main():
    if not DEVICE:
        raise SystemExit("set RUNLUCKY_DEVICE to one of your device ids first")
    user = os.environ["RUNLUCKY_USER"]
    password = os.environ["RUNLUCKY_PASS"]
    async with aiohttp.ClientSession() as s:
        c = api.RunLuckyClient(s, user, password)
        await c.async_login()
        variants = [
            {"deviceId": DEVICE},
            {"deviceId": DEVICE, "model": 1, "regenerationPattern": 0},
            {"deviceId": DEVICE, "deviceModel": 1, "regenerationPattern": 0},
            {"deviceId": DEVICE, "model": "1", "regenerationPattern": "0"},
            {"deviceId": DEVICE, "model": 1},
        ]
        for params in variants:
            r = await c._async_request(
                "GET",
                f"{api.API_DEVICE_LOOKUP}/get-device-model-setting",
                params=params,
            )
            true_keys = [k for k, v in (r or {}).items() if v is True]
            print(
                f"{json.dumps({k: v for k, v in params.items() if k != 'deviceId'})}"
                f" -> model={r.get('deviceModel')} regen={r.get('regenerationPattern')}"
                f" true={len(true_keys)} {true_keys}"
            )

        print("\nlive query-device-info-return-result:")
        try:
            q = await c.async_query_device(DEVICE)
            pd = q.get("protocolData") or {}
            print("keys:", len(pd))
            print(json.dumps({k: pd[k] for k in list(pd)[:8]}, ensure_ascii=False))
            print("station:", pd.get("station"), "flowRate:", pd.get("flowRate"))
        except Exception as e:
            print("query failed:", type(e).__name__, e)


asyncio.run(main())
