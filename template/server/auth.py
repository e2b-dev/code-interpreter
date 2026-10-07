import httpx
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from envs import ENVD_PORT


class AccessTokenVerifier:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def verify(self, token: str) -> int:
        if not token or not token.isascii():
            return 401
        try:
            response = await self.client.get(
                f"http://127.0.0.1:{ENVD_PORT}/auth",
                headers={"X-Access-Token": token},
            )
        except httpx.HTTPError:
            return 503

        if response.status_code == 204:
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
