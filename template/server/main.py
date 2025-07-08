import logging
import sys
import uuid
import httpx

from typing import Dict, Union, Literal, Set

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from api.models.context import Context
from api.models.create_context import CreateContext
from api.models.execution_request import ExecutionRequest
from consts import JUPYTER_BASE_URL
from contexts import create_context, normalize_language
from messaging import ContextWebSocket
from stream import StreamingListJsonResponse
from utils.locks import LockedMap
from envs import get_envs

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.Logger(__name__)
http_logger = logging.getLogger("httpcore.http11")
http_logger.setLevel(logging.WARNING)


websockets: Dict[Union[str, Literal["default"]], ContextWebSocket] = {}
default_websockets = LockedMap()
global client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient()

    try:
        default_context = await create_context(client, websockets, "python", "/home/user")
        default_websockets["python"] = default_context.id
        websockets["default"] = websockets[default_context.id]

        logger.info("Connected to default runtime")
        yield

        # Will cleanup after application shuts down
        for ws in websockets.values():
            await ws.close()

        await client.aclose()
    except Exception as e:
        logger.error(f"Failed to initialize default context: {e}")
        raise


app = FastAPI(lifespan=lifespan)

logger.info("Starting Code Interpreter server")


@app.get("/health")
async def get_health():
    return "OK"


@app.post("/execute")
async def post_execute(request: ExecutionRequest):
    logger.info(f"Executing code: {request.code}")

    if request.context_id and request.language:
        return PlainTextResponse(
            "Only one of context_id or language can be provided",
            status_code=400,
        )

    context_id = None
    if request.language:
        language = normalize_language(request.language)

        async with await default_websockets.get_lock(language):
            context_id = default_websockets.get(language)

            if not context_id:
                try:
                    context = await create_context(
                        client, websockets, language, "/home/user"
                    )
                except Exception as e:
                    return PlainTextResponse(str(e), status_code=500)

                context_id = context.id
                default_websockets[language] = context_id

    elif request.context_id:
        context_id = request.context_id

    if context_id:
        ws = websockets.get(context_id, None)
    else:
        ws = websockets["default"]

    if not ws:
        return PlainTextResponse(
            f"Context {request.context_id} not found",
            status_code=404,
        )

    # set global env vars if not set on first execution
    if not ws.global_env_vars:
        ws.global_env_vars = await get_envs()
        await ws.set_env_vars(ws.global_env_vars)

    return StreamingListJsonResponse(
        ws.execute(
            request.code,
            env_vars=request.env_vars,
        )
    )


@app.post("/contexts")
async def post_contexts(request: CreateContext) -> Context:
    logger.info(f"Creating a new context")

    language = normalize_language(request.language)
    cwd = request.cwd or "/home/user"

    try:
        return await create_context(client, websockets, language, cwd)
    except Exception as e:
        return PlainTextResponse(str(e), status_code=500)


@app.get("/contexts")
async def get_contexts() -> Set[Context]:
    logger.info(f"Listing contexts")

    context_ids = websockets.keys()

    return set(
        Context(
            id=websockets[context_id].context_id,
            language=websockets[context_id].language,
            cwd=websockets[context_id].cwd,
        )
        for context_id in context_ids
    )


@app.post("/contexts/{context_id}/restart")
async def restart_context(context_id: str) -> None:
    logger.info(f"Restarting context {context_id}")

    ws = websockets.get(context_id, None)
    if not ws:
        return PlainTextResponse(
            f"Context {context_id} not found",
            status_code=404,
        )

    session_id = ws.session_id

    await ws.close()

    response = await client.post(
        f"{JUPYTER_BASE_URL}/api/kernels/{ws.context_id}/restart"
    )
    if not response.is_success:
        return PlainTextResponse(
            f"Failed to restart context {context_id}",
            status_code=500,
        )

    ws = ContextWebSocket(
        ws.context_id,
        session_id,
        ws.language,
        ws.cwd,
    )

    await ws.connect()

    websockets[context_id] = ws


@app.delete("/contexts/{context_id}")
async def remove_context(context_id: str) -> None:
    logger.info(f"Removing context {context_id}")

    ws = websockets.get(context_id, None)
    if not ws:
        return PlainTextResponse(
            f"Context {context_id} not found",
            status_code=404,
        )

    try:
        await ws.close()
    except:
        pass

    response = await client.delete(f"{JUPYTER_BASE_URL}/api/kernels/{ws.context_id}")
    if not response.is_success:
        return PlainTextResponse(
            f"Failed to remove context {context_id}",
            status_code=500,
        )

    del websockets[context_id]
