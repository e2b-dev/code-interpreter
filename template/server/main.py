import asyncio
import logging
import uuid
import httpx

from typing import Dict, Union
from pydantic import StrictStr
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.models.create_kernel import CreateKernel
from api.models.execution_request import ExecutionRequest
from messaging import JupyterKernelWebSocket
from stream import StreamingLisJsonResponse


logger = logging.Logger(__name__)

logging.basicConfig(level=logging.DEBUG)


session_id = str(uuid.uuid4())

websockets: Dict[Union[str, StrictStr], JupyterKernelWebSocket] = {}

with open("/root/.jupyter/kernel_id") as file:
    kernel_id = file.read().strip()

client = httpx.AsyncClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    default_ws = JupyterKernelWebSocket(
        f"ws://localhost:8888/api/kernels/{kernel_id}/channels", session_id
    )

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

    data = {
        "path": str(uuid.uuid4()),
        "kernel": {"name": kernel_name},
        "type": "notebook",
        "name": str(uuid.uuid4()),
    }
    logger.debug(f"Creating kernel with data: {data}")

    response = await client.post("http://localhost:8888/api/sessions", json=data)

    if not response.is_success:
        raise Exception(f"Failed to create kernel: {response.text}")

    session_data = response.json()
    sess_id = session_data["id"]
    _id = session_data["kernel"]["id"]

    response = await client.patch(
        f"http://localhost:8888/api/sessions/{sess_id}",
        json={"path": cwd},
    )
    if not response.is_success:
        raise Exception(f"Failed to create kernel: {response.text}")

    logger.debug(f"Created kernel {kernel_id}")

    ws = JupyterKernelWebSocket(
        f"ws://localhost:8888/api/kernels/{kernel_id}/channels", session_id
    )
    task = asyncio.create_task(ws.connect())
    await ws.started

    websockets[_id] = ws

    return kernel_id
