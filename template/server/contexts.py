import logging
import uuid
from typing import Optional

import httpx

from api.models.context import Context
from fastapi.responses import PlainTextResponse

from consts import JUPYTER_BASE_URL
from errors import ExecutionError
from messaging import ContextWebSocket, FailedContextException

logger = logging.Logger(__name__)


def normalize_language(language: Optional[str]) -> str:
    if not language:
        return "python"

    language = language.lower().strip()

    if language == "js":
        return "javascript"

    return language


async def create_context(
    client: httpx.AsyncClient, websockets: dict, language: str, cwd: str
) -> Context:
    data = {
        "path": str(uuid.uuid4()),
        "kernel": {"name": language},
        "type": "notebook",
        "name": str(uuid.uuid4()),
    }
    logger.debug(f"Creating new {language} context")

    response = await client.post(f"{JUPYTER_BASE_URL}/api/sessions", json=data)

    if not response.is_success:
        raise Exception(
            f"Failed to create context: {response.text}",
        )

    session_data = response.json()
    session_id = session_data["id"]
    context_id = session_data["kernel"]["id"]

    logger.debug(f"Created context {context_id}")

    for _ in range(3):
        ws = ContextWebSocket(context_id, session_id, language, cwd)
        try:
            await ws.connect()
        except FailedContextException as e:
            logger.error(f"Failed to create context: {e}")
            await restart_context(ws, client)
        break
    else:
        raise Exception("Failed to create context")

    websockets[context_id] = ws

    logger.info(f"Setting working directory to {cwd}")
    try:
        await ws.change_current_directory(cwd, language)
    except ExecutionError as e:
        return PlainTextResponse(
            "Failed to set working directory",
            status_code=500,
        )

    return Context(language=language, id=context_id, cwd=cwd)


async def restart_context(
    ws: ContextWebSocket, client: httpx.AsyncClient
) -> ContextWebSocket:
    try:
        await ws.close()
    except:
        print("Failed to close", ws.context_id)
        pass

    response = await client.post(
        f"{JUPYTER_BASE_URL}/api/kernels/{ws.context_id}/restart"
    )
    if not response.is_success:
        return PlainTextResponse(
            f"Failed to restart context {ws.context_id}",
            status_code=500,
        )

    ws = ContextWebSocket(
        ws.context_id,
        ws.session_id,
        ws.language,
        ws.cwd,
    )

    try:
        await ws.connect()
    except Exception as e:
        print("Connection error", e)
        raise e

    return ws
