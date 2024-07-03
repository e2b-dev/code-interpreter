import uuid

from fastapi import FastAPI

from messaging import JupyterKernelWebSocket
from models.execution import Execution
from models.execution_request import ExecutionRequest

app = FastAPI()


session_id = str(uuid.uuid4())

with open("/root/.jupyter/kernel_id") as file:
    kernel_id = file.read().strip()

ws = JupyterKernelWebSocket(f"localhost:8888/api/kernels/{kernel_id}/channels", session_id)
ws.connect()

@app.get("/health")
def health():
    return "Request was successful"


@app.post("/execute", response_model=Execution)
def execute(request: ExecutionRequest):
    return ws.execute(code=request.code)
