import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

import requests
from fastapi import FastAPI

from api.models.create_kernel import CreateKernel, RestartKernel
from messaging import JupyterKernelWebSocket
from api.models.execution_request import ExecutionRequest
from stream import StreamingLisJsonResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.Logger(__name__)

websockets: Dict[str, JupyterKernelWebSocket] = {}
global default_kernel_id


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
def health():
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

    kernel_name = request.kernel_name or "python3"
    cwd = request.cwd or "/home/user"

    data = {"path": str(uuid.uuid4()), "kernel": {"name": kernel_name}, "type": "notebook", "name": str(uuid.uuid4())}
    logger.debug(f"Creating kernel with data: {data}")

    response = requests.post("http://localhost:8888/api/sessions",json=data)
    if not response.ok:
        raise Exception(f"Failed to create kernel: {response.text}")

    session_data = response.json()
    session_id = session_data["id"]
    kernel_id = session_data["kernel"]["id"]

    response = requests.patch(f"http://localhost:8888/api/sessions/{session_id}", json={"path": cwd})
    if not response.ok:
        raise Exception(f"Failed to create kernel: {response.text}")

    logger.debug(f"Created kernel {kernel_id}")

    ws = JupyterKernelWebSocket(kernel_id, session_id)
    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[kernel_id] = ws

    return kernel_id


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
        raise Exception(f"Kernel {kernel_id} not found")

    kernel_id = ws.kernel_id
    session_id = ws.session_id

    await ws.close()

    response = requests.post(f"http://localhost:8888/api/kernels/{kernel_id}/restart")
    if not response.ok:
        raise Exception(f"Failed to restart kernel {kernel_id}")

    ws = JupyterKernelWebSocket(kernel_id, session_id)

    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[kernel_id] = ws
