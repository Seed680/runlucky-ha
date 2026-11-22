#!/usr/bin/env python3
"""Standalone CLI to poke the RunLucky (润莱智联) cloud API.

Useful for debugging the integration without a running Home Assistant.

    python tools/runlucky_cli.py login
    python tools/runlucky_cli.py devices
    python tools/runlucky_cli.py data <deviceId>
    python tools/runlucky_cli.py control <deviceId> key=value [key=value ...]
    python tools/runlucky_cli.py regen <deviceId>
    python tools/runlucky_cli.py vacation <deviceId> on|off

Credentials are read from RUNLUCKY_USER / RUNLUCKY_PASS environment variables.
The access token is cached in .runlucky_token.json next to this script.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

try:  # inside a HA checkout / HA installed
    from custom_components.runlucky.api import (  # noqa: E402
        RunLuckyApiError,
        RunLuckyAuthError,
        RunLuckyClient,
    )
except ModuleNotFoundError:  # homeassistant not installed: load api.py alone
    import importlib.util
    import types

    _PKG_DIR = REPO / "custom_components" / "runlucky"
    _pkg = types.ModuleType("rl_cli")
    _pkg.__path__ = [str(_PKG_DIR)]
    sys.modules["rl_cli"] = _pkg

    def _load(name: str):
        spec = importlib.util.spec_from_file_location(
            f"rl_cli.{name}", _PKG_DIR / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    _load("const")
    _api = _load("api")
    RunLuckyApiError = _api.RunLuckyApiError
    RunLuckyAuthError = _api.RunLuckyAuthError
    RunLuckyClient = _api.RunLuckyClient

TOKEN_CACHE = Path(__file__).with_name(".runlucky_token.json")


def _creds() -> tuple[str, str]:
    user = os.environ.get("RUNLUCKY_USER")
    password = os.environ.get("RUNLUCKY_PASS")
    if not user or not password:
        sys.exit("set RUNLUCKY_USER and RUNLUCKY_PASS first")
    return user, password


async def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    user, password = _creds()

    async with aiohttp.ClientSession() as session:
        client = RunLuckyClient(session, user, password)
        try:
            token = await client.async_login()
            if cmd == "login":
                print(json.dumps({k: v for k, v in token.items() if k != "access_token"},
                                 indent=2, ensure_ascii=False))
                print("access_token:", token["access_token"][:24], "...")
                return 0

            if cmd == "devices":
                devices = await client.async_get_devices()
                print(json.dumps(devices, indent=2, ensure_ascii=False))
                return 0

            if cmd == "data" and len(argv) >= 3:
                device_id = argv[2]
                payload = await client.async_get_device_data(device_id)
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                return 0

            if cmd == "query" and len(argv) >= 3:
                payload = await client.async_query_device(argv[2])
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                return 0

            if cmd == "control" and len(argv) >= 4:
                device_id = argv[2]
                body = {}
                for pair in argv[3:]:
                    key, _, value = pair.partition("=")
                    try:
                        body[key] = json.loads(value)
                    except ValueError:
                        body[key] = value
                await client.async_control(device_id, body)
                print("OK", body)
                return 0

            if cmd == "regen" and len(argv) >= 3:
                await client.async_forced_regeneration(argv[2])
                print("OK")
                return 0

            if cmd == "vacation" and len(argv) >= 4:
                if argv[3] == "on":
                    await client.async_enter_vacation(argv[2])
                else:
                    await client.async_exit_vacation(argv[2])
                print("OK")
                return 0

            if cmd == "pressure" and len(argv) >= 4:
                await client.async_set_pressure(argv[2], float(argv[3]))
                print("OK")
                return 0

            if cmd == "modelsetting" and len(argv) >= 3:
                print(json.dumps(await client.async_get_model_setting(argv[2], None, None),
                                 indent=2, ensure_ascii=False))
                return 0

            print(__doc__)
            return 2
        except RunLuckyAuthError as err:
            print("AUTH ERROR:", err)
            return 1
        except RunLuckyApiError as err:
            print("API ERROR:", err)
            return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))
