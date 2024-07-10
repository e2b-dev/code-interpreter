import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from messaging import JupyterKernelWebSocket
from api.models.execution_request import ExecutionRequest
from stream import StreamingLisJsonResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.Logger(__name__)


session_id = str(uuid.uuid4())

websockets: Dict[str, JupyterKernelWebSocket] = {}

with open("/root/.jupyter/kernel_id") as file:
    kernel_id = file.read().strip()


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

    ws = websockets["default"]

    return StreamingLisJsonResponse(ws.execute(request.code))
