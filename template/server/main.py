import asyncio
import logging
import uuid
import httpx

from typing import Dict, Union, Literal, List
from pydantic import StrictStr
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from api.models.context import Context
from api.models.create_kernel import CreateContext
from api.models.execution_request import ExecutionRequest
from messaging import JupyterKernelWebSocket
from stream import StreamingListJsonResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.Logger(__name__)
http_logger = logging.getLogger("httpcore.http11")
http_logger.setLevel(logging.WARNING)

websockets: Dict[Union[str, StrictStr, Literal["default"]], JupyterKernelWebSocket] = {}
global default_kernel_id


global client

# TODO: Increase timeout for requests to allow streaming, increase max request/response sizes to acommodate larger results, Increase keepalive timeout
# TODO: Handle pings from server so we can keep the connection from idling
# TODO: Check https://www.uvicorn.org/deployment/#running-behind-nginx | Why do we need to run behind nginx?
# TODO: Think about what to return from this API so later we can change only the SDK (not the API) when we change methods


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient()

    # Load the default kernel
    session_id = str(uuid.uuid4())

    global default_kernel_id
    with open("/root/.jupyter/kernel_id") as file:
        default_kernel_id = file.read().strip()

    default_ws = JupyterKernelWebSocket(default_kernel_id, session_id, "python")

    websockets["default"] = default_ws

    logger.info("Connecting to default runtime")
    _ = asyncio.create_task(default_ws.connect())
    await default_ws.started

    logger.info("Connected to default runtime")
    yield

    for ws in websockets.values():
        await ws.close()

    await client.aclose()


app = FastAPI(lifespan=lifespan)

logger.info("Starting Code Interpreter server")


@app.get("/health")
async def health():
    return "Request was successful"


@app.post("/execute")
async def execute(request: ExecutionRequest):
    logger.info(f"Executing code: {request.code}")

    if request.kernel_id:
        ws = websockets.get(request.kernel_id, websockets["default"])
    else:
        ws = websockets["default"]

    return StreamingListJsonResponse(ws.execute(request.code))


@app.post("/contexts")
async def create_context(request: CreateContext) -> Context:
    logger.info(f"Creating new kernel for language: {request.language}")

    kernel_name = request.language or "python3"
    cwd = request.cwd or "/home/user"

    data = {
        "path": str(uuid.uuid4()),
        "kernel": {"name": kernel_name},
        "type": "notebook",
        "name": str(uuid.uuid4()),
    }
    logger.debug(f"Creating kernel with data: {data}")

    response = await client.post("http://localhost:8888/api/sessions", json=data)

    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create kernel: {response.text}",
        )

    session_data = response.json()
    session_id = session_data["id"]
    kernel_id = session_data["kernel"]["id"]

    response = await client.patch(
        f"http://localhost:8888/api/sessions/{session_id}", json={"path": cwd}
    )
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create kernel: {response.text}",
        )

    logger.debug(f"Created kernel {kernel_id}")

    ws = JupyterKernelWebSocket(kernel_id, session_id, kernel_name)
    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[kernel_id] = ws

    return Context(name=kernel_name, id=kernel_id)


@app.get("/contexts")
async def list_contexts() -> List[Context]:
    logger.info(f"Listing contexts")

    kernel_ids = list(websockets.keys())

    return [
        Context(
            id=websockets[kernel_id].kernel_id,
            name=websockets[kernel_id].name,
        )
        for kernel_id in kernel_ids
    ]


@app.post("/contexts/{context_id}/restart")
async def restart_context(context_id: str) -> None:
    logger.info(f"Restarting context {context_id}")

    ws = websockets.get(context_id, None)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"Kernel {context_id} not found",
        )

    session_id = ws.session_id

    await ws.close()

    response = await client.post(
        f"http://localhost:8888/api/kernels/{ws.kernel_id}/restart"
    )
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart context {context_id}",
        )

    ws = JupyterKernelWebSocket(ws.kernel_id, session_id, ws.name)

    _ = asyncio.create_task(ws.connect())
    await ws.started

    websockets[context_id] = ws


@app.delete("/contexts/{context_id}")
async def remove_context(context_id: str) -> None:
    logger.info(f"Removing context {context_id}")

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

    response = await client.delete(f"http://localhost:8888/api/kernels/{ws.kernel_id}")
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove context {context_id}",
        )

    del websockets[context_id]
