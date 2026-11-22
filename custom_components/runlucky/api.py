"""Async client for the RunLucky (润莱智联) cloud API.

Reverse engineered from the official app (com.runxin.runlucky) / its Vue
front-end.  The back-end is an ABP Framework application secured with
OpenIddict:

    POST /connect/token                       (password grant)
    GET  /api/run-lucky/device/app/...        (Bearer token)

All list responses are wrapped as ``{"result": {"items": [...], "totalCount": n}}``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_BASE,
    API_DEVICE,
    API_DEVICE_CONTROL,
    API_DEVICE_LOOKUP,
    API_FAMILY,
    API_FAMILY_DEVICE,
    CLIENT_ID,
    SCOPE,
    TOKEN_PATH,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class RunLuckyAuthError(Exception):
    """Raised when authentication fails."""


class RunLuckyApiError(Exception):
    """Generic API failure."""


class RunLuckyClient:
    """Thin async wrapper around the RunLucky cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        *,
        base_url: str = API_BASE,
    ) -> None:
        """Initialise the client."""
        self._session = session
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._scope = SCOPE
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # authentication
    # ------------------------------------------------------------------
    @property
    def token_valid(self) -> bool:
        """Return True if the cached access token can still be used."""
        return bool(self._access_token) and time.monotonic() < self._expires_at - 60

    async def async_login(self) -> dict[str, Any]:
        """Authenticate with the password grant and cache the token."""
        token = await self._async_token_request(
            {
                "grant_type": "password",
                "scope": self._scope,
                "username": self._username,
                "password": self._password,
                "client_id": CLIENT_ID,
            }
        )
        self._store_token(token)
        return token

    async def async_ensure_token(self) -> None:
        """Make sure a valid access token is available."""
        if self.token_valid:
            return
        async with self._lock:
            if self.token_valid:
                return
            if self._refresh_token:
                try:
                    token = await self._async_token_request(
                        {
                            "grant_type": "refresh_token",
                            "refresh_token": self._refresh_token,
                            "client_id": CLIENT_ID,
                        }
                    )
                    self._store_token(token)
                    return
                except RunLuckyAuthError as err:
                    _LOGGER.debug("Refresh token rejected (%s), re-login", err)
                    self._refresh_token = None
            await self.async_login()

    async def _async_token_request(self, payload: dict[str, str]) -> dict[str, Any]:
        url = f"{self._base_url}{TOKEN_PATH}"
        try:
            async with self._session.post(
                url, data=payload, timeout=REQUEST_TIMEOUT
            ) as resp:
                body = await self._async_json(resp)
                if resp.status == 200 and body.get("access_token"):
                    return body
                error = body.get("error") or resp.status
                description = body.get("error_description") or body.get("message") or ""
                raise RunLuckyAuthError(f"{error}: {description}")
        except aiohttp.ClientError as err:
            raise RunLuckyApiError(f"Cannot reach {url}: {err}") from err

    def _store_token(self, token: dict[str, Any]) -> None:
        self._access_token = token["access_token"]
        self._refresh_token = token.get("refresh_token") or self._refresh_token
        expires_in = int(token.get("expires_in") or 3600)
        self._expires_at = time.monotonic() + expires_in

    # ------------------------------------------------------------------
    # low level request helpers
    # ------------------------------------------------------------------
    async def _async_json(self, resp: aiohttp.ClientResponse) -> dict[str, Any]:
        text = await resp.text()
        if not text:
            return {}
        try:
            data = await resp.json(content_type=None)
        except ValueError:
            return {"raw": text}
        return data if isinstance(data, dict) else {"result": data}

    async def _async_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Any:
        """Perform an authenticated request and return the unwrapped result."""
        await self.async_ensure_token()
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-Hans",
        }
        clean_params = {
            k: v for k, v in (params or {}).items() if v is not None and v != ""
        }
        try:
            async with self._session.request(
                method,
                url,
                params=clean_params or None,
                json=body,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                payload = await self._async_json(resp)
                if resp.status == 401:
                    self._access_token = None
                    await self.async_ensure_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.request(
                        method,
                        url,
                        params=clean_params or None,
                        json=body,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT,
                    ) as retry:
                        payload = await self._async_json(retry)
                        resp = retry
                if resp.status >= 400:
                    raise RunLuckyApiError(self._error_message(payload, resp.status))
                if payload.get("success") is False:
                    raise RunLuckyApiError(self._error_message(payload, resp.status))
                if "result" in payload:
                    return payload["result"]
                return payload
        except aiohttp.ClientError as err:
            raise RunLuckyApiError(f"{path}: {err}") from err

    @staticmethod
    def _error_message(payload: dict[str, Any], status: int) -> str:
        error = payload.get("error")
        if isinstance(error, dict):
            msg = error.get("message") or error.get("details")
            if msg:
                return str(msg)
        if isinstance(error, str):
            return payload.get("error_description") or error
        return payload.get("message") or payload.get("raw") or f"HTTP {status}"

    @staticmethod
    def _items(result: Any) -> list[dict[str, Any]]:
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            items = result.get("items")
            if isinstance(items, list):
                return items
            # single object
            return [result]
        return []

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    async def async_get_profile(self) -> dict[str, Any]:
        result = await self._async_request("GET", "/api/basic-data/app/profile")
        return result if isinstance(result, dict) else {}

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return every device visible to the account."""
        try:
            result = await self._async_request(
                "GET", f"{API_DEVICE_LOOKUP}/get-device-list"
            )
            devices = self._items(result)
            if devices:
                return devices
        except RunLuckyApiError as err:
            _LOGGER.debug("device-lookup failed (%s), trying families", err)

        devices = []
        seen: set[str] = set()
        try:
            families = self._items(await self._async_request("GET", f"{API_FAMILY}/"))
        except RunLuckyApiError as err:
            _LOGGER.debug("family list failed: %s", err)
            families = []

        for family in families:
            family_id = family.get("id")
            if not family_id:
                continue
            try:
                result = await self._async_request(
                    "GET",
                    f"{API_FAMILY_DEVICE}/get-list-by-family-id",
                    params={"familyId": family_id},
                )
            except RunLuckyApiError as err:
                _LOGGER.debug("family %s device list failed: %s", family_id, err)
                continue
            for device in self._items(result):
                device.setdefault("familyId", family_id)
                device.setdefault("familyName", family.get("familyName") or family.get("name"))
                device_id = device.get("deviceId") or device.get("id")
                if device_id and device_id not in seen:
                    seen.add(device_id)
                    devices.append(device)
        return devices

    async def async_get_device_data(self, device_id: str) -> dict[str, Any]:
        """Return the cached device record including ``protocolData``."""
        result = await self._async_request(
            "GET", f"{API_DEVICE}/get-device-with--data", params={"id": device_id}
        )
        return result if isinstance(result, dict) else {}

    async def async_query_device(self, device_id: str) -> dict[str, Any]:
        """Ask the cloud to poll the physical device (slow, blocks the device)."""
        result = await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/query-device-info-return-result",
            params={"id": device_id},
        )
        return result if isinstance(result, dict) else {}

    async def async_get_model_setting(
        self, device_id: str, model: int | str | None, regeneration_pattern: int | str | None
    ) -> dict[str, Any]:
        """Return the per-model list of supported settings."""
        result = await self._async_request(
            "GET",
            f"{API_DEVICE_LOOKUP}/get-device-model-setting",
            params={
                "deviceId": device_id,
                "model": model,
                "regenerationPattern": regeneration_pattern,
            },
        )
        return result if isinstance(result, dict) else {}

    async def async_control(self, device_id: str, payload: dict[str, Any]) -> None:
        """Write one or more protocol parameters."""
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/control-device",
            params={"id": device_id},
            body=payload,
        )

    async def async_forced_regeneration(self, device_id: str) -> None:
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/forced-regeneration",
            params={"id": device_id},
        )

    async def async_ro_forced_regeneration(self, device_id: str) -> None:
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/ro-forced-regeneration",
            params={"id": device_id},
        )

    async def async_enter_vacation(self, device_id: str) -> None:
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/change-vacation",
            params={"id": device_id},
        )

    async def async_exit_vacation(self, device_id: str) -> None:
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/exit-vacation",
            params={"id": device_id},
        )

    async def async_set_pressure(self, device_id: str, value: float) -> None:
        await self._async_request(
            "POST",
            f"{API_DEVICE_CONTROL}/set-pressure-setting-value",
            params={"id": device_id},
            body={"pressureSettingValue": value},
        )

    async def async_sync_clock(self, device_id: str, time_str: str) -> None:
        await self.async_control(device_id, {"currentTime": time_str})

    async def async_close(self) -> None:
        """No-op placeholder; the session is owned by Home Assistant."""
