import uuid

from fastapi import FastAPI
from starlette.responses import JSONResponse

from messaging import JupyterKernelWebSocket
from api.models.execution import Execution
from api.models.execution_request import ExecutionRequest

app = FastAPI()


session_id = str(uuid.uuid4())

with open("/root/.jupyter/kernel_id") as file:
    kernel_id = file.read().strip()

ws = JupyterKernelWebSocket(
    f"ws://localhost:8888/api/kernels/{kernel_id}/channels", session_id
)
ws.connect()


@app.get("/health")
def health():
    return "Request was successful"


@app.post("/execute", response_model=Execution)
def execute(request: ExecutionRequest) -> JSONResponse:
    result = ws.execute(code=request.code)
    return JSONResponse(content=result)
