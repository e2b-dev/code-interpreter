import asyncio
import logging
import uuid
import httpx

from typing import Dict, Union, Literal
from pydantic import StrictStr
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from api.models.create_kernel import CreateKernel, RestartKernel, ShutdownKernel
from messaging import JupyterKernelWebSocket
from api.models.execution_request import ExecutionRequest
from messaging import JupyterKernelWebSocket
from stream import StreamingLisJsonResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.Logger(__name__)

websockets: Dict[Union[str, StrictStr, Literal["default"]], JupyterKernelWebSocket] = {}
global default_kernel_id


client = httpx.AsyncClient()

# TODO: Increase keepalive timeout
# TODO: Increase timeout for requests to allow streaming
# TODO: Handle pings from server so we can keep the connection from idling
# TODO: Check https://www.uvicorn.org/deployment/#running-behind-nginx
# TODO: Update signatures and types on clients
# TODO: Think about what to return from this API so later we can change only the SDK (not the API) when we change methods
# TODO: Return objects not just plain types from api (list kernels) so we can expand it later with more data (kernel language, cwd, etc.)
# TODO: Should we use kernel ids as context ids and have /contexts/{context_id}/restart, etc?


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the default kernel
    session_id = str(uuid.uuid4())

    global default_kernel_id
    with open("/root/.jupyter/kernel_id") as file:
        default_kernel_id = file.read().strip()

    default_ws = JupyterKernelWebSocket(default_kernel_id, session_id)

    websockets["default"] = default_ws
    websockets["python"] = default_ws

    logger.info("Connecting to default runtime")
    task = asyncio.create_task(default_ws.connect())
    await default_ws.started

    logger.info("Connected to default runtime")
    yield

    await default_ws.close()
    task.cancel()


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

    return StreamingLisJsonResponse(ws.execute(request.code))


@app.post("/contexts")
async def create_kernel(request: CreateKernel):
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

    ws = JupyterKernelWebSocket(kernel_id, session_id)
    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[kernel_id] = ws

    return {"kernel_id": kernel_id}


@app.get("/contexts")
async def list_kernels():
    logger.info(f"Listing kernels")

    kernel_ids = list(websockets.keys())
    kernel_ids.remove(default_kernel_id)

    return kernel_ids


@app.post("/contexts/restart")
async def restart_kernel(request: RestartKernel):
    logger.info(f"Restarting kernel")

    kernel_id = request.kernel_id or "default"

    ws = websockets.get(kernel_id, None)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"Kernel {kernel_id} not found",
        )

    kernel_id = ws.kernel_id
    session_id = ws.session_id

    await ws.close()

    response = await client.post(
        f"http://localhost:8888/api/kernels/{kernel_id}/restart"
    )
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart kernel {kernel_id}",
        )

    ws = JupyterKernelWebSocket(kernel_id, session_id)

    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[kernel_id] = ws


@app.delete("/contexts")
async def shutdown_kernel(request: ShutdownKernel):
    logger.info(f"Shutting down kernel")

    kernel_id = request.kernel_id or "default"

    ws = websockets.get(kernel_id, None)
    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"Kernel {kernel_id} not found",
        )

    kernel_id = ws.kernel_id

    try:
        await ws.close()
    except:
        pass

    response = await client.delete(f"http://localhost:8888/api/kernels/{kernel_id}")
    if not response.is_success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to shutdown kernel {kernel_id}",
        )

    del websockets[kernel_id]
