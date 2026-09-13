from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import httpx

from recall_desk.ports import NotFound, Permanent, Transient, UnknownOutcome


JsonResponse = dict[str, Any] | list[Any]
T = TypeVar("T")


class ApiClient:
    """One-attempt HTTP client that translates transport failures to port errors."""

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str],
        base_params: dict[str, str] | None = None,
        default_retry_after_s: float | None = None,
        timeout_s: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.default_retry_after_s = default_retry_after_s
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            params=base_params,
            timeout=timeout_s,
            transport=transport,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        params: dict[str, str] | None = None,
        is_write: bool,
    ) -> JsonResponse:
        try:
            response = self._client.request(method, path, json=json, params=params)
        except (httpx.ConnectError, httpx.ConnectTimeout) as error:
            raise Transient(retry_after=None, before_send=True) from error
        except (httpx.TimeoutException, httpx.ProtocolError) as error:
            if is_write:
                raise UnknownOutcome() from error
            raise Transient(retry_after=None, before_send=False) from error

        if response.status_code == 429:
            raise Transient(
                retry_after=_retry_after(response.headers.get("Retry-After"), self.default_retry_after_s),
                before_send=False,
            )
        if response.status_code >= 500:
            raise Transient(retry_after=None, before_send=False)
        if response.status_code == 404:
            raise NotFound(status=response.status_code, body=response.text)
        if 400 <= response.status_code < 500:
            raise Permanent(status=response.status_code, body=response.text)

        return response.json()


def _retry_after(value: str | None, default: float | None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def read_with_retry(fn: Callable[[], T], max_retries: int, sleep: Callable[[float], Any]) -> T:
    retries = 0
    while True:
        try:
            return fn()
        except Transient as error:
            if retries >= max_retries:
                raise
            retries += 1
            sleep(error.retry_after if error.retry_after is not None else 0)
