import asyncio
import hashlib
from contextlib import suppress

import httpx
import pytest
from anyio import fail_after
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import auth
import main


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(main.access_token, "digest", None)
    monkeypatch.setattr(main.access_token, "connected", False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://interpreter"
    ) as client:
        yield client


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/execute"),
        ("POST", "/contexts"),
        ("GET", "/contexts"),
        ("DELETE", "/contexts/missing"),
        ("POST", "/contexts/missing/restart"),
        ("GET", "/docs"),
    ],
)
async def test_endpoints_require_current_token(client, method, path):
    response = await client.request(method, path)
    assert response.status_code == 503
    main.access_token.digest = hashlib.sha512(b"sandbox-token").digest()
    for token in ("", "incorrect", main.access_token.digest.hex()):
        response = await client.request(method, path, headers={"X-Access-Token": token})
        assert response.status_code == 401


async def test_health_requires_delivery_connection_but_no_bearer(client):
    assert (await client.get("/health")).status_code == 503
    main.access_token.connected = True
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/contexts")).status_code == 503


def test_public_websockets_are_not_exposed():
    with pytest.raises(WebSocketDisconnect) as exc:
        with TestClient(main.app).websocket_connect("/api/kernels/kernel/channels"):
            pytest.fail("Jupyter must not be exposed through the public server")
    assert exc.value.code == 1008


async def test_socket_updates_revoke_old_token_and_disconnect_fails_closed(
    client, tmp_path, monkeypatch
):
    path = str(tmp_path / "auth.sock")
    monkeypatch.setattr(auth, "TOKEN_SOCKET", path)
    connections = asyncio.Queue()

    async def connected(reader, writer):
        await connections.put((reader, writer))

    server = await asyncio.start_unix_server(connected, path=path)
    task = asyncio.create_task(main.access_token.subscribe())
    try:
        reader, writer = await asyncio.wait_for(connections.get(), 2)
        for current, previous in (
            ("parent-token", "wrong"),
            ("child-token", "parent-token"),
        ):
            writer.write(hashlib.sha512(current.encode()).hexdigest().encode() + b"\n")
            await writer.drain()
            assert await asyncio.wait_for(reader.readexactly(1), 2) == b"+"
            assert (
                await client.get("/contexts", headers={"X-Access-Token": current})
            ).status_code == 200
            assert (
                await client.get("/contexts", headers={"X-Access-Token": previous})
            ).status_code == 401

        writer.close()
        await writer.wait_closed()
        with fail_after(2):
            while main.access_token.connected:
                await asyncio.sleep(0.01)
        assert (
            await client.get("/contexts", headers={"X-Access-Token": "child-token"})
        ).status_code == 503

        reader, writer = await asyncio.wait_for(connections.get(), 3)
        writer.write(hashlib.sha512(b"child-token").hexdigest().encode() + b"\n")
        await writer.drain()
        assert await asyncio.wait_for(reader.readexactly(1), 2) == b"+"
        assert (
            await client.get("/contexts", headers={"X-Access-Token": "child-token"})
        ).status_code == 200

        writer.write(b"\n")
        await writer.drain()
        assert await asyncio.wait_for(reader.readexactly(1), 2) == b"+"
        assert (await client.get("/contexts")).status_code == 503
        writer.write(b"invalid verifier\n")
        await writer.drain()
        assert await asyncio.wait_for(reader.read(), 2) == b""
        assert (await client.get("/health")).status_code == 503
        writer.close()
        await writer.wait_closed()
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        server.close()
        await server.wait_closed()
