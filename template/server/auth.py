import asyncio
import hashlib
import hmac
import logging
from contextlib import suppress

from starlette.requests import Request
from starlette.responses import PlainTextResponse

TOKEN_SOCKET = "/run/e2b-auth/token.sock"
logger = logging.getLogger(__name__)


class AccessToken:
    def __init__(self):
        self.digest = None
        self.connected = False

    def accepts(self, token: str) -> bool:
        return bool(
            self.digest
            and token
            and hmac.compare_digest(
                self.digest, hashlib.sha512(token.encode("utf-8")).digest()
            )
        )

    async def subscribe(self):
        while True:
            writer = None
            try:
                reader, writer = await asyncio.open_unix_connection(
                    TOKEN_SOCKET, limit=129
                )
                while True:
                    line = await reader.readline()
                    if line == b"\n":
                        self.digest = None
                    elif len(line) == 129 and line.endswith(b"\n"):
                        digest = bytes.fromhex(line[:-1].decode("ascii"))
                        if len(digest) != 64:
                            raise ValueError("Invalid token verifier")
                        self.digest = digest
                    else:
                        raise ValueError("Invalid token verifier")
                    self.connected = True
                    writer.write(b"+")
                    await writer.drain()
            except (OSError, ValueError, UnicodeError):
                logger.warning("Local authentication connection unavailable")
            finally:
                self.digest = None
                self.connected = False
                if writer is not None:
                    writer.close()
                    with suppress(OSError):
                        await writer.wait_closed()
            await asyncio.sleep(1)


class EnvdAuthMiddleware:
    def __init__(self, app, access_token: AccessToken, local: bool = False):
        self.app = app
        self.access_token = access_token
        self.local = local

    async def __call__(self, scope, receive, send):
        if (
            self.local
            or scope["type"] not in ("http", "websocket")
            or (
                scope["type"] == "http"
                and scope["method"] == "GET"
                and scope["path"] == "/health"
            )
        ):
            await self.app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return

        token = Request(scope).headers.get("X-Access-Token", "")
        if not self.access_token.accepts(token):
            status = 401 if self.access_token.digest else 503
            response = PlainTextResponse(
                "Unauthorized" if status == 401 else "Authentication unavailable",
                status_code=status,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
