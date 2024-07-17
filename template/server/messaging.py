import json
import logging
import uuid
import asyncio

from asyncio import Queue
from typing import (
    Dict,
    Optional,
    Union,
)
from pydantic import StrictStr
from websockets.client import WebSocketClientProtocol, connect

from api.models.error import Error
from api.models.logs import Stdout, Stderr
from api.models.result import Result
from api.models.output import EndOfExecution, NumberOfExecutions, OutputType


logger = logging.getLogger(__name__)


class Execution:
    def __init__(self):
        self.queue = Queue[
            Union[
                Result,
                Error,
                Stdout,
                Stderr,
                EndOfExecution,
                NumberOfExecutions,
            ]
        ]()
        self.input_accepted = False


class JupyterKernelWebSocket:
    _ws: Optional[WebSocketClientProtocol] = None

    def __init__(
        self,
        kernel_id: str,
        session_id: str,
        name: str,
        cwd: str,
    ):
        self.name = name
        self.cwd = cwd
        self.kernel_id = kernel_id
        self.url = f"ws://localhost:8888/api/kernels/{kernel_id}/channels"
        self.session_id = session_id

        self._executions: Dict[str, Execution] = {}

    async def connect(self):
        logger.debug(f"WebSocket connecting to {self.url}")

        ws_logger = logger.getChild("websockets.client")
        ws_logger.setLevel(logging.ERROR)

        self._ws = await connect(
            self.url,
            max_size=None,
            max_queue=None,
            logger=ws_logger,
        )

        logger.info(f"WebSocket connected to {self.url}")
        self._receive_task = asyncio.create_task(
            self._receive_message(),
            name="receive_message",
        )

    def _get_execute_request(self, msg_id: str, code: Union[str, StrictStr]) -> str:
        return json.dumps(
            {
                "header": {
                    "msg_id": msg_id,
                    "username": "e2b",
                    "session": self.session_id,
                    "msg_type": "execute_request",
                    "version": "5.3",
                },
                "parent_header": {},
                "metadata": {},
                "content": {
                    "code": code,
                    "silent": False,
                    "store_history": True,
                    "user_expressions": {},
                    "allow_stdin": False,
                },
            }
        )

    async def execute(self, code: Union[str, StrictStr]):
        message_id = str(uuid.uuid4())
        logger.debug(f"Sending execution for code ({message_id}): {code}")

        self._executions[message_id] = Execution()
        request = self._get_execute_request(message_id, code)

        if self._ws is None:
            raise Exception("WebSocket not connected")

        await self._ws.send(request)

        queue = self._executions[message_id].queue
        while True:
            output = await queue.get()
            if output.type == OutputType.END_OF_EXECUTION:
                break

            logger.debug(f"Got result for code ({message_id}): {output}")
            yield output.model_dump(exclude_none=True)

        del self._executions[message_id]

    async def _receive_message(self):
        if not self._ws:
            logger.error("No WebSocket connection")
            return

        try:
            async for message in self._ws:
                logger.debug(f"WebSocket received message: {message}".strip())
                await self._process_message(json.loads(message))
        except Exception as e:
            logger.error(f"WebSocket received error while receiving messages: {e}")

    async def _process_message(self, data: dict):
        """
        Process messages from the WebSocket

        Message types:
        https://jupyter-client.readthedocs.io/en/stable/messaging.html

        :param data: The message data
        """

        parent_msg_ig = data["parent_header"].get("msg_id", None)
        if parent_msg_ig is None:
            logger.warning("Parent message ID not found. %s", data)
            return

        logger.debug(f"Received message {data['msg_type']} for {parent_msg_ig}")

        execution = self._executions.get(parent_msg_ig)
        if not execution:
            return

        queue = execution.queue
        if data["msg_type"] == "error":
            logger.debug(f"Cell {parent_msg_ig} finished execution with error")
            await queue.put(
                Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback="".join(data["content"]["traceback"]),
                )
            )

        elif data["msg_type"] == "stream":
            if data["content"]["name"] == "stdout":
                await queue.put(
                    Stdout(
                        text=data["content"]["text"], timestamp=data["header"]["date"]
                    )
                )

            elif data["content"]["name"] == "stderr":
                await queue.put(
                    Stderr(
                        text=data["content"]["text"], timestamp=data["header"]["date"]
                    )
                )

        elif data["msg_type"] in "display_data":
            await queue.put(Result(is_main_result=False, data=data["content"]["data"]))
        elif data["msg_type"] == "execute_result":
            await queue.put(Result(is_main_result=True, data=data["content"]["data"]))
        elif data["msg_type"] == "status":
            if data["content"]["execution_state"] == "idle":
                if execution.input_accepted:
                    logger.debug(f"Cell {parent_msg_ig} finished execution")
                    await queue.put(EndOfExecution())

            elif data["content"]["execution_state"] == "error":
                logger.debug(f"Cell {parent_msg_ig} finished execution with error")
                await queue.put(
                    Error(
                        name=data["content"]["ename"],
                        value=data["content"]["evalue"],
                        traceback="".join(data["content"]["traceback"]),
                    )
                )
                await queue.put(EndOfExecution())

        elif data["msg_type"] == "execute_reply":
            if data["content"]["status"] == "error":
                logger.debug(f"Cell {parent_msg_ig} finished execution with error")
                await queue.put(
                    Error(
                        name=data["content"]["ename"],
                        value=data["content"]["evalue"],
                        traceback="".join(data["content"]["traceback"]),
                    )
                )
            elif data["content"]["status"] == "ok":
                pass

        elif data["msg_type"] == "execute_input":
            logger.debug(f"Input accepted for {parent_msg_ig}")
            await queue.put(
                NumberOfExecutions(execution_count=data["content"]["execution_count"])
            )
            execution.input_accepted = True
        else:
            logger.warning(f"[UNHANDLED MESSAGE TYPE]: {data['msg_type']}")

    async def close(self):
        logger.debug(f"Closing WebSocket {self.kernel_id}")

        if self._ws is not None:
            await self._ws.close()

        self._receive_task.cancel()

        for execution in self._executions.values():
            execution.queue.put_nowait(EndOfExecution())
