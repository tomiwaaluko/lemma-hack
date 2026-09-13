from __future__ import annotations

import httpx
import pytest

from recall_desk.adapters.live.http import ApiClient, read_with_retry
from recall_desk.ports import NotFound, Permanent, Transient, UnknownOutcome


def _client(handler, **kwargs) -> ApiClient:
    return ApiClient(
        "https://api.example.test",
        {"Authorization": "Bearer test"},
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_HC1_write_read_timeout_is_unknown_outcome():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(UnknownOutcome):
        _client(handler).request("PATCH", "/blocks/b1", is_write=True)


def test_HC2_read_read_timeout_is_transient():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(Transient) as error:
        _client(handler).request("GET", "/blocks/b1", is_write=False)

    assert error.value.before_send is False


def test_HC3_rate_limit_uses_retry_after_header():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "7"}, request=request)

    with pytest.raises(Transient) as error:
        _client(handler, default_retry_after_s=30).request("GET", "/blocks/b1", is_write=False)

    assert error.value.retry_after == 7


def test_HC4_rate_limit_uses_default_retry_after_when_header_is_absent():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, request=request)

    with pytest.raises(Transient) as error:
        _client(handler, default_retry_after_s=30).request("GET", "/blocks/b1", is_write=False)

    assert error.value.retry_after == 30


def test_HC5_not_found_response_is_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing", request=request)

    with pytest.raises(NotFound):
        _client(handler).request("GET", "/blocks/b1", is_write=False)


def test_HC6_other_client_error_preserves_status_and_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text='{"error":"bad request"}', request=request)

    with pytest.raises(Permanent) as error:
        _client(handler).request("GET", "/blocks/b1", is_write=False)

    assert error.value.status == 400
    assert error.value.body == '{"error":"bad request"}'


def test_HC7_connect_error_before_write_is_transient_before_send():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unable to connect", request=request)

    with pytest.raises(Transient) as error:
        _client(handler).request("PATCH", "/blocks/b1", is_write=True)

    assert error.value.before_send is True


def test_HC8_read_with_retry_retries_transient_twice_then_returns_value():
    attempts = 0
    sleeps: list[float] = []

    def fn() -> dict[str, str]:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Transient(retry_after=2, before_send=False)
        return {"result": "ok"}

    assert read_with_retry(fn, max_retries=2, sleep=sleeps.append) == {"result": "ok"}
    assert sleeps == [2, 2]
