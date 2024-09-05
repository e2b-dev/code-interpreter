import logging
import uuid
import httpx

from typing import Dict, Union, Literal, List

from pydantic import StrictStr
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from api.models.context import Context
from api.models.create_context import CreateContext
from api.models.execution_request import ExecutionRequest
from errors import ExecutionError
from messaging import JupyterKernelWebSocket
from stream import StreamingListJsonResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.Logger(__name__)
http_logger = logging.getLogger("httpcore.http11")
http_logger.setLevel(logging.WARNING)


JUPYTER_BASE_URL = "http://localhost:8888"

websockets: Dict[Union[StrictStr, Literal["default"]], JupyterKernelWebSocket] = {}
global default_kernel_id
global client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient()

    global default_kernel_id
    with open("/root/.jupyter/kernel_id") as file:
        default_kernel_id = file.read().strip()

    default_ws = JupyterKernelWebSocket(
        default_kernel_id,
        str(uuid.uuid4()),
        "python",
        "/home/user",
    )

    logger.info("Connecting to default runtime")
    await default_ws.connect()

    websockets["default"] = default_ws

    logger.info("Connected to default runtime")
    yield

    for ws in websockets.values():
        await ws.close()

    await client.aclose()


app = FastAPI(lifespan=lifespan)

logger.info("Starting Code Interpreter server")


@app.get("/health")
async def health():
    return "OK"


@app.post("/execute")
async def execute(request: ExecutionRequest):
    logger.info(f"Executing code: {request.code}")

    if request.context_id:
        ws = websockets.get(request.context_id)

        if not ws:
            raise HTTPException(
                status_code=404,
                detail=f"Kernel {request.context_id} not found",
            )
    else:
        ws = websockets["default"]

    return StreamingListJsonResponse(
        ws.execute(request.code, env_vars=request.env_vars)
    )


@app.post("/contexts")
async def create_context(request: CreateContext) -> Context:
    logger.info(f"Creating new kernel")

    data = {
        "path": str(uuid.uuid4()),
        "kernel": {"name": request.name},
        "type": "notebook",
        "name": str(uuid.uuid4()),
    }
    logger.debug(f"Creating new kernel with data: {data}")

    response = await client.post(f"{JUPYTER_BASE_URL}/api/sessions", json=data)

    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create kernel: {response.text}",
        )

    session_data = response.json()
    session_id = session_data["id"]
    kernel_id = session_data["kernel"]["id"]

    logger.debug(f"Created kernel {kernel_id}")

    ws = JupyterKernelWebSocket(
        kernel_id,
        session_id,
        request.name,
        request.cwd,
    )
    await ws.connect()

    websockets[kernel_id] = ws

    if request.cwd:
        logger.info(f"Setting working directory to {request.cwd}")
        try:
            await ws.change_current_directory(request.cwd)
        except ExecutionError as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to set working directory",
            ) from e

    return Context(name=request.name, id=kernel_id, cwd=request.cwd)


@app.get("/contexts")
async def list_contexts() -> List[Context]:
    logger.info(f"Listing kernels")

    kernel_ids = list(websockets.keys())

    return [
        Context(
            id=websockets[kernel_id].kernel_id,
            name=websockets[kernel_id].name,
            cwd=websockets[kernel_id].cwd,
        )
        for kernel_id in kernel_ids
    ]


@app.post("/contexts/{context_id}/restart")
async def restart_context(context_id: str) -> None:
    logger.info(f"Restarting kernel {context_id}")

    ws = websockets.get(context_id, None)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"Kernel {context_id} not found",
        )

    session_id = ws.session_id

    await ws.close()

    response = await client.post(
        f"{JUPYTER_BASE_URL}/api/kernels/{ws.kernel_id}/restart"
    )
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart kernel {context_id}",
        )

    ws = JupyterKernelWebSocket(
        ws.kernel_id,
        session_id,
        ws.name,
        ws.cwd,
    )

    await ws.connect()

    websockets[context_id] = ws


@app.delete("/contexts/{context_id}")
async def remove_context(context_id: str) -> None:
    logger.info(f"Removing kernel {context_id}")

    ws = websockets.get(context_id, None)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"Kernel {context_id} not found",
        )

    try:
        await ws.close()
    except:
        pass

    response = await client.delete(f"{JUPYTER_BASE_URL}/api/kernels/{ws.kernel_id}")
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove context {context_id}",
        )

    del websockets[context_id]
