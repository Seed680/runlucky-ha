"""Offline tests for the RunLucky API client (mock cloud server).

Run with:  python -m pytest tests -q      (or)  python tests/test_api.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import aiohttp
from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The integration package imports Home Assistant at package level, so load the
# two modules we need as a stand-alone synthetic package to keep this test
# dependency free.
import importlib.util  # noqa: E402
import types  # noqa: E402

_PKG_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "runlucky"
_pkg = types.ModuleType("rl_under_test")
_pkg.__path__ = [str(_PKG_DIR)]
sys.modules["rl_under_test"] = _pkg


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"rl_under_test.{name}", _PKG_DIR / f"{name}.py"
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

STATE: dict = {}


def _envelope(result):
    return web.json_response({"result": result, "success": True, "error": None})


async def token_handler(request: web.Request) -> web.Response:
    form = await request.post()
    STATE.setdefault("token_requests", []).append(dict(form))
    if form.get("grant_type") == "refresh_token":
        if form.get("refresh_token") != "the-refresh-token":
            return web.json_response({"error": "invalid_grant"}, status=400)
        return web.json_response(
            {"access_token": "refreshed-token", "expires_in": 3600, "token_type": "Bearer"}
        )
    if form.get("username") != "user@example.com" or form.get("password") != "secret":
        return web.json_response(
            {"error": "invalid_grant", "error_description": "用户名或密码错误!"}, status=400
        )
    STATE["logins"] = STATE.get("logins", 0) + 1
    return web.json_response(
        {
            "access_token": f"token-{STATE['logins']}",
            "expires_in": 3600,
            "token_type": "Bearer",
            "refresh_token": "the-refresh-token",
            "scope": "RunLuckyIot",
        }
    )


async def device_list_handler(request: web.Request) -> web.Response:
    if request.headers.get("Authorization") != f"Bearer token-{STATE['logins']}":
        return web.json_response({"error": "invalid_token"}, status=401)
    return _envelope(
        {
            "totalCount": 1,
            "items": [
                {
                    "deviceId": "dev-123",
                    "deviceName": "软水机",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "isEnableFlowStatistics": True,
                }
            ],
        }
    )


async def device_data_handler(request: web.Request) -> web.Response:
    STATE["last_query"] = dict(request.query)
    if request.query.get("id") != "dev-123":
        return web.json_response({"error": {"message": "bad id"}}, status=400)
    return _envelope(
        {
            "id": "dev-123",
            "deviceName": "软水机",
            "protocolData": {
                "deviceModel": 13,
                "station": 0,
                "flowRate": 1.5,
                "waterVolumeUnit": 1,
                "residualWaterProduction": 320,
                "residualWaterProductionUnit": 1,
                "remainingDay": 12,
                "saltShortageReminder": 0,
                "regenerationPattern": 0,
            },
        }
    )


async def control_handler(request: web.Request) -> web.Response:
    STATE["last_query"] = dict(request.query)
    STATE["last_body"] = await request.json()
    return _envelope(True)


async def ok_handler(request: web.Request) -> web.Response:
    STATE["last_query"] = dict(request.query)
    return _envelope(True)


async def make_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/connect/token", token_handler)
    app.router.add_get(
        "/api/run-lucky/device/app/device-lookup/get-device-list", device_list_handler
    )
    app.router.add_get(
        "/api/run-lucky/device/app/device/get-device-with--data", device_data_handler
    )
    app.router.add_post(
        "/api/run-lucky/device/app/device-control/control-device", control_handler
    )
    app.router.add_post(
        "/api/run-lucky/device/app/device-control/forced-regeneration", ok_handler
    )
    return app


async def main() -> int:
    runner = web.AppRunner(await make_app())
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    base = f"http://127.0.0.1:{port}"

    failures = 0

    def check(name, cond, extra=""):
        nonlocal failures
        if cond:
            print(f"  ok   {name}")
        else:
            failures += 1
            print(f"  FAIL {name} {extra}")

    async with aiohttp.ClientSession() as session:
        client = RunLuckyClient(session, "user@example.com", "secret", base_url=base)

        print("login")
        token = await client.async_login()
        check("access_token", token["access_token"] == "token-1", token)
        check("refresh_token kept", client._refresh_token == "the-refresh-token")
        check(
            "form fields",
            STATE["token_requests"][0]
            == {
                "grant_type": "password",
                "scope": "RunLuckyIot",
                "username": "user@example.com",
                "password": "secret",
                "client_id": "RunLuckyIot_App",
            },
            STATE["token_requests"][0],
        )

        print("devices")
        devices = await client.async_get_devices()
        check("unwrapped items", len(devices) == 1 and devices[0]["deviceId"] == "dev-123", devices)

        print("device data")
        data = await client.async_get_device_data("dev-123")
        check("query id", STATE["last_query"] == {"id": "dev-123"}, STATE["last_query"])
        check("protocolData", data["protocolData"]["station"] == 0, data)

        print("control")
        await client.async_control("dev-123", {"rawWaterHardness": 300})
        check("control query", STATE["last_query"] == {"id": "dev-123"})
        check("control body", STATE["last_body"] == {"rawWaterHardness": 300}, STATE["last_body"])

        print("forced regeneration")
        await client.async_forced_regeneration("dev-123")
        check("regen query", STATE["last_query"] == {"id": "dev-123"})

        print("token refresh on expiry")
        client._expires_at = 0  # force refresh
        await client.async_ensure_token()
        check("used refresh grant", STATE["token_requests"][-1]["grant_type"] == "refresh_token")
        check("new token", client._access_token == "refreshed-token")

        print("bad credentials")
        bad = RunLuckyClient(session, "user@example.com", "wrong", base_url=base)
        try:
            await bad.async_login()
            check("raises auth error", False)
        except RunLuckyAuthError as err:
            check("raises auth error", "invalid_grant" in str(err), str(err))

        print("http error surfaces")
        try:
            await client.async_get_device_data("nope")
            check("api error", False)
        except RunLuckyApiError as err:
            check("api error", "bad id" in str(err), str(err))

    await runner.cleanup()
    print()
    print("ALL TESTS PASSED" if failures == 0 else f"{failures} FAILURE(S)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
