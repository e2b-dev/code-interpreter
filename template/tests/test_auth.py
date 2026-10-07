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
    state = SimpleNamespace(token="valid-token", calls=[], status=None)
    monkeypatch.setattr(main, "websockets", {})

    async def envd(request):
        assert str(request.url) == "http://127.0.0.1:49983/auth"
        state.calls.append(request)
        await asyncio.sleep(0)
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


async def test_each_request_is_validated(server):
    client, state = server
    for _ in range(2):
        response = await client.get(
            "/contexts", headers={"X-Access-Token": state.token}
        )
        assert response.status_code == 200
        assert response.json() == []
    assert len(state.calls) == 2


async def test_token_rotation_and_revocation_apply_to_next_request(server):
    client, state = server
    headers = {"X-Access-Token": state.token}
    response = await client.get("/contexts", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    state.token = "rotated-token"

    assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 2
    assert (
        await client.get("/contexts", headers={"X-Access-Token": state.token})
    ).status_code == 200
    assert len(state.calls) == 3
    assert (await client.get("/contexts", headers=headers)).status_code == 401
    headers = {"X-Access-Token": state.token}
    state.token = None
    assert (await client.get("/contexts", headers=headers)).status_code == 401
    assert len(state.calls) == 5


async def test_concurrent_requests_are_validated_individually(server):
    client, state = server
    responses = await asyncio.gather(
        *[
            client.get("/contexts", headers={"X-Access-Token": state.token})
            for _ in range(10)
        ]
    )
    assert all(response.status_code == 200 for response in responses)
    assert len(state.calls) == 10


@pytest.mark.parametrize(
    "failure", [200, 302, 404, 500, 503, httpx.ConnectError("offline")]
)
async def test_envd_failures_reject_previously_valid_token_and_recover(server, failure):
    client, state = server
    headers = {"X-Access-Token": state.token}
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    state.status = failure
    for _ in range(2):
        assert (await client.get("/contexts", headers=headers)).status_code == 503
    assert len(state.calls) == 3
    state.status = None
    assert (await client.get("/contexts", headers=headers)).status_code == 200
    assert len(state.calls) == 4


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


async def test_malformed_headers_are_rejected_without_calling_envd(server):
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
