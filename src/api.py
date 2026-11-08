"""Small client for the Hackatime API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://hackatime.hackclub.com/api/hackatime/v1"


class HackatimeError(RuntimeError):
    """Raised when a Hackatime request fails."""


class HackatimeClient:
    def __init__(self, api_key: str, user: str = "current", timeout: float = 20.0):
        self.api_key = api_key
        self.user = user
        self.timeout = timeout

    def _get(self, path: str) -> dict[str, Any]:
        query = urlencode({"api_key": self.api_key})
        request = Request(
            f"{BASE_URL}{path}?{query}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "hackfetch/0.1.0",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as exc:
            detail = _error_detail(exc)
            if exc.code == 401:
                raise HackatimeError(
                    "Unauthorized (401). Check that your Hackatime API key is valid."
                ) from exc
            raise HackatimeError(f"Hackatime returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise HackatimeError(f"Could not reach Hackatime: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise HackatimeError("Hackatime returned a response that was not valid JSON.") from exc

        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise HackatimeError("Hackatime returned an unexpected response shape.")
        return data

    def statusbar_today(self) -> dict[str, Any]:
        return self._get(f"/users/{quote(self.user, safe='')}/statusbar/today")

    def stats_last_7_days(self) -> dict[str, Any]:
        return self._get(f"/users/{quote(self.user, safe='')}/stats/last_7_days")


def _error_detail(exc: HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return exc.reason

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip() or exc.reason

    if isinstance(payload, dict):
        for key in ("error", "message", "detail"):
            value = payload.get(key)
            if value:
                return str(value)
    return raw.strip() or exc.reason
