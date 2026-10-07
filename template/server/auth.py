import asyncio
import hashlib
import hmac
import time

import httpx
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from envs import ENVD_PORT

CACHE_TTL = 5.0


class AccessTokenVerifier:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.digest = b""
        self.validated_at = (0.0, 0.0)
        self.lock = asyncio.Lock()

    def cached(self, digest: bytes) -> bool:
        monotonic, wall = self.validated_at
        return (
            hmac.compare_digest(self.digest, digest)
            and 0 <= time.monotonic() - monotonic < CACHE_TTL
            and 0 <= time.time() - wall < CACHE_TTL
        )

    async def verify(self, token: str) -> int:
        try:
            encoded = token.encode("ascii")
        except UnicodeEncodeError:
            return 401
        if not encoded:
            return 401
        digest = hashlib.sha256(encoded).digest()
        if self.cached(digest):
            return 204

        async with self.lock:
            if self.cached(digest):
                return 204

            # Start the lease before I/O so a slow response cannot extend it.
            validated_at = (time.monotonic(), time.time())
            try:
                response = await self.client.get(
                    f"http://127.0.0.1:{ENVD_PORT}/auth",
                    headers={"X-Access-Token": token},
                )
            except httpx.HTTPError:
                return 503

            if response.status_code == 204:
                self.digest = digest
                self.validated_at = validated_at
                return 204
            return 401 if response.status_code == 401 else 503


class EnvdAuthMiddleware:
    def __init__(self, app: ASGIApp, local: bool = False):
        self.app = app
        self.local = local

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket" and not self.local:
            await send({"type": "websocket.close", "code": 1008})
            return

        if (
            scope["type"] != "http"
            or self.local
            or (scope["method"] == "GET" and scope["path"] == "/health")
        ):
            await self.app(scope, receive, send)
            return

        tokens = Headers(scope=scope).getlist("x-access-token")
        status = 401
        if len(tokens) == 1:
            verifier = getattr(scope["app"].state, "access_token_verifier", None)
            status = await verifier.verify(tokens[0]) if verifier else 503

        if status != 204:
            response = PlainTextResponse(
                "Unauthorized" if status == 401 else "Authentication unavailable",
                status_code=status,
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
