import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from messaging import JupyterKernelWebSocket
from api.models.execution import Execution
from api.models.execution_request import ExecutionRequest

logger = logging.Logger(__name__)
logger.setLevel(logging.DEBUG)


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


@app.post("/execute", response_model=Execution, response_model_exclude_none=True)
async def execute(request: ExecutionRequest) -> Execution:
    logger.info(f"Executing code: {request.code}")

    ws = websockets["default"]
    execution = await ws.execute(code=request.code)

    logger.info(f"Execution result: {execution}")
    return execution
