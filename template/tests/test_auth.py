import asyncio
from types import SimpleNamespace

import httpx
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import auth
import main


@pytest.fixture
async def server(monkeypatch):
    state = SimpleNamespace(
        token="valid-token",
        calls=[],
        status=None,
        monotonic=100.0,
        wall=1000.0,
        latency=0,
    )
    monkeypatch.setattr(
        auth,
        "time",
        SimpleNamespace(monotonic=lambda: state.monotonic, time=lambda: state.wall),
    )
    monkeypatch.setattr(main, "websockets", {})

    async def envd(request):
        assert str(request.url) == "http://127.0.0.1:49983/auth"
        state.calls.append(request)
        await asyncio.sleep(0)
        state.monotonic += state.latency
        state.wall += state.latency
        if isinstance(state.status, Exception):
            raise state.status
        status = state.status
        if status is None:
            status = 204 if request.headers["X-Access-Token"] == state.token else 401
        return httpx.Response(status)

    async with httpx.AsyncClient(transport=httpx.MockTransport(envd)) as upstream:
        monkeypatch.setattr(
            main.app.state,
            "access_token_verifier",
            auth.AccessTokenVerifier(upstream),
            raising=False,
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app), base_url="http://server"
        ) as client:
            yield client, state


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/execute"),
        ("POST", "/contexts"),
        ("GET", "/contexts"),
        ("POST", "/contexts/id/restart"),
        ("DELETE", "/contexts/id"),
        ("GET", "/docs"),
    ],
)
async def test_requests_require_auth_before_route_handling(server, method, path):
    client, state = server
    for headers in ({}, {"X-Access-Token": "wrong"}):
        response = await client.request(method, path, headers=headers)
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    assert len(state.calls) == 1


async def test_cache_expires_without_sliding_and_replaces_rotated_token(server):
    client, state = server
    headers = {"X-Access-Token": state.token}
    response = await client.get("/contexts", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    state.token = "rotated-token"

    state.monotonic += 4
    state.wall += 4
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    assert len(state.calls) == 1

    state.monotonic += 1
    state.wall += 1
    assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 2
    assert (
        await client.get("/contexts", headers={"X-Access-Token": state.token})
    ).status_code == 200
    assert len(state.calls) == 3
    assert (await client.get("/contexts", headers=headers)).status_code == 401


async def test_concurrent_requests_share_validation_and_wrong_tokens_cannot_hit_cache(
    server,
):
    client, state = server
    responses = await asyncio.gather(
        *[
            client.get("/contexts", headers={"X-Access-Token": state.token})
            for _ in range(10)
        ]
    )
    assert all(response.status_code == 200 for response in responses)
    assert len(state.calls) == 1
    for _ in range(2):
        assert (
            await client.get("/contexts", headers={"X-Access-Token": "wrong"})
        ).status_code == 401
    assert len(state.calls) == 3
    assert (
        await client.get("/contexts", headers={"X-Access-Token": state.token})
    ).status_code == 200
    assert len(state.calls) == 3


@pytest.mark.parametrize(
    "failure", [200, 302, 404, 500, 503, httpx.ConnectError("offline")]
)
async def test_expired_cache_fails_closed_and_recovers(server, failure):
    client, state = server
    headers = {"X-Access-Token": state.token}
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    state.monotonic += 5
    state.wall += 5
    state.status = failure
    for _ in range(2):
        assert (await client.get("/contexts", headers=headers)).status_code == 503
    assert len(state.calls) == 3
    state.status = None
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    assert len(state.calls) == 4


@pytest.mark.parametrize(
    "clock,delta", [("wall", 10), ("wall", -10), ("monotonic", -10)]
)
async def test_clock_jumps_invalidate_cached_validation(server, clock, delta):
    client, state = server
    headers = {"X-Access-Token": state.token}
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    setattr(state, clock, getattr(state, clock) + delta)
    state.token = "rotated-token"
    assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 2


async def test_health_and_cors_preflight_do_not_require_auth(server):
    client, state = server
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/health/")).status_code == 401
    response = await client.options(
        "/contexts",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Access-Token",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert not state.calls


async def test_slow_response_does_not_extend_cache_lifetime(server):
    client, state = server
    state.latency = 5
    headers = {"X-Access-Token": state.token}
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    state.token = "rotated-token"
    assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 2


async def test_malformed_headers_cannot_use_cached_validation(server):
    client, state = server
    assert (
        await client.get("/contexts", headers={"X-Access-Token": state.token})
    ).status_code == 200
    for headers in (
        [("X-Access-Token", state.token), ("X-Access-Token", "wrong")],
        [(b"X-Access-Token", b"\xff")],
        {"X-Access-Token": ""},
    ):
        assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 1


def test_public_websockets_are_rejected():
    with pytest.raises(WebSocketDisconnect) as exc:
        with TestClient(main.app).websocket_connect("/contexts"):
            pytest.fail("public websocket accepted")
    assert exc.value.code == 1008
