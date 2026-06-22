"""Anonymous HTTP client: browser fingerprint, rate-limiting, actionable errors."""
from __future__ import annotations

import time

from .config import HTTP_TIMEOUT, IMPERSONATE, RATE_LIMIT_MIN_INTERVAL
from .errors import CloudflareBlocked, NotFound, UpstreamError


def classify_block(status: int, headers: dict, body: str) -> None:
    """Raise the appropriate exception if the response is unusable; otherwise do nothing."""
    lower = {str(k).lower(): str(v) for k, v in headers.items()}
    is_cf = "cf-mitigated" in lower or "just a moment" in body.lower()
    if status == 403 and is_cf:
        raise CloudflareBlocked()
    if status == 404:
        raise NotFound()
    if not (200 <= status < 300):
        raise UpstreamError(f"HTTP {status} from VeryChic.")
    return None


def _make_session():
    from curl_cffi import requests  # lazy import (network only needed at runtime)
    return requests.Session(impersonate=IMPERSONATE)


class VeryChicClient:
    def __init__(self, *, session=None, min_interval: float = RATE_LIMIT_MIN_INTERVAL,
                 timeout: int = HTTP_TIMEOUT, clock=time.monotonic, sleep=time.sleep):
        self._session = session if session is not None else _make_session()
        self._min_interval = min_interval
        self._timeout = timeout
        self._clock = clock
        self._sleep = sleep
        self._last = None  # timestamp of the last request

    def _respect_rate_limit(self) -> None:
        if self._last is not None:
            elapsed = self._clock() - self._last
            wait = self._min_interval - elapsed
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def get_json(self, url: str, params: dict | None = None):
        self._respect_rate_limit()
        resp = self._session.get(url, params=params, timeout=self._timeout)
        classify_block(resp.status_code, dict(resp.headers), resp.text or "")
        try:
            return resp.json()
        except Exception as exc:
            raise UpstreamError("Non-JSON response from VeryChic.") from exc

    def get_text(self, url: str, params: dict | None = None) -> str:
        self._respect_rate_limit()
        resp = self._session.get(url, params=params, timeout=self._timeout)
        classify_block(resp.status_code, dict(resp.headers), resp.text or "")
        return resp.text or ""
