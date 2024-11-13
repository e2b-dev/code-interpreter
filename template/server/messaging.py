import datetime
import json
import logging
import uuid
import asyncio

from asyncio import Queue, Future
from envs import get_envs
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
from api.models.output import (
    EndOfExecution,
    NumberOfExecutions,
    OutputType,
    UnexpectedEndOfExecution,
)
from errors import ExecutionError

logger = logging.getLogger(__name__)


class Execution:
    def __init__(self, in_background: bool = False):
        self.queue = Queue[
            Union[
                Result,
                Error,
                Stdout,
                Stderr,
                EndOfExecution,
                NumberOfExecutions,
                UnexpectedEndOfExecution,
            ]
        ]()
        self.input_accepted = False
        self.errored = False
        self.in_background = in_background


class FailedContextException(Exception):
    pass


class ContextWebSocket:
    _ws: Optional[WebSocketClientProtocol] = None
    _receive_task: Optional[asyncio.Task] = None

    def __init__(
        self,
        context_id: str,
        session_id: str,
        language: str,
        cwd: str,
    ):
        self.language = language
        self.cwd = cwd
        self.context_id = context_id
        self.url = f"ws://localhost:8888/api/kernels/{context_id}/channels?session_id={session_id}"
        self.session_id = session_id
        self.ready = Future()

        self._executions: Dict[str, Execution] = {}
        self._lock = asyncio.Lock()

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

        try:  # Wait for the context to be ready
            await asyncio.wait_for(self.ready, timeout=5)

        except asyncio.TimeoutError:
            logger.error("Context is not ready")
            raise FailedContextException("Context is not ready")

    def _get_execute_request(
        self, msg_id: str, code: Union[str, StrictStr], background: bool
    ) -> str:
        return json.dumps(
            {
                "header": {
                    "msg_id": msg_id,
                    "username": "e2b",
                    "session": self.session_id,
                    "msg_type": "execute_request",
                    "version": "5.3",
                    "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
                "parent_header": {},
                "metadata": {
                    "trusted": True,
                    "deletedCells": [],
                    "recordTiming": False,
                    "cellId": str(uuid.uuid4()),
                },
                "content": {
                    "code": code,
                    "silent": background,
                    "store_history": True,
                    "user_expressions": {},
                    "stop_on_error": True,
                    "allow_stdin": False,
                },
                "channel": "shell",
            }
        )

    async def _wait_for_result(self, message_id: str):
        queue = self._executions[message_id].queue

        while True:
            output = await queue.get()
            if output.type == OutputType.END_OF_EXECUTION:
                break

            if output.type == OutputType.UNEXPECTED_END_OF_EXECUTION:
                logger.error(f"Unexpected end of execution for code ({message_id})")
                yield Error(
                    name="UnexpectedEndOfExecution",
                    value="Connection to the execution was closed before the execution was finished",
                    traceback="",
                )
                break

            yield output.model_dump(exclude_none=True)

    async def change_current_directory(
        self, path: Union[str, StrictStr], language: str
    ):
        message_id = str(uuid.uuid4())
        self._executions[message_id] = Execution(in_background=True)
        if language == "python":
            request = self._get_execute_request(message_id, f"%cd {path}", True)
        elif language == "deno":
            request = self._get_execute_request(
                message_id, f"Deno.chdir('{path}')", True
            )
        elif language == "js":
            request = self._get_execute_request(
                message_id, f"process.chdir('{path}')", True
            )
        elif language == "r":
            request = self._get_execute_request(message_id, f"setwd('{path}')", True)
        elif language == "java":
            request = self._get_execute_request(
                message_id, f"System.setProperty('user.dir', '{path}')", True
            )
        else:
            return

        await self._ws.send(request)

        async for item in self._wait_for_result(message_id):
            if item["type"] == "error":
                raise ExecutionError(f"Error during execution: {item}")

    async def execute(
        self,
        code: Union[str, StrictStr],
        env_vars: Dict[StrictStr, str] = None,
    ):
        message_id = str(uuid.uuid4())
        logger.debug(f"Sending code for the execution ({message_id}): {code}")

        self._executions[message_id] = Execution()

        if self._ws is None:
            raise Exception("WebSocket not connected")

        global_env_vars = get_envs()
        env_vars = {**global_env_vars, **env_vars} if env_vars else global_env_vars
        async with self._lock:
            if env_vars:
                vars_to_set = {**global_env_vars, **env_vars}

                # if there is an indent in the code, we need to add the env vars at the beginning of the code
                lines = code.split("\n")
                indent = 0
                for i, line in enumerate(lines):
                    if line.strip() != "":
                        indent = len(line) - len(line.lstrip())
                        break

                if self.language == "python":
                    code = (
                        indent * " "
                        + f"os.environ.set_envs_for_execution({vars_to_set})\n"
                        + code
                    )

            logger.info(code)
            request = self._get_execute_request(message_id, code, False)

            # Send the code for execution
            await self._ws.send(request)

            # Stream the results
            async for item in self._wait_for_result(message_id):
                yield item

            del self._executions[message_id]

    async def _receive_message(self):
        if not self._ws:
            logger.error("No WebSocket connection")
            return

        try:
            async for message in self._ws:
                try:
                    await self._process_message(json.loads(message))
                except Exception as e:
                    logger.error(
                        f"WebSocket received error while receiving messages: {str(e)}"
                    )
        except Exception as e:
            logger.error(f"WebSocket error while receiving messages: {str(e)}")

    async def _process_message(self, data: dict):
        """
        Process messages from the WebSocket

        Message types:
        https://jupyter-client.readthedocs.io/en/stable/messaging.html

        :param data: The message data
        """
        if (
            data["msg_type"] == "status"
            and data["content"]["execution_state"] == "restarting"
        ):
            logger.error("Context is restarting")
            for execution in self._executions.values():
                await execution.queue.put(
                    Error(
                        name="ContextRestarting",
                        value="Context was restarted",
                        traceback="",
                    )
                )
                await execution.queue.put(EndOfExecution())
            return

        if data["msg_type"] == "status":
            print(f"[{self.context_id}]: {data['content']['execution_state']}")
            if data["content"]["execution_state"] == "idle":
                if not self.ready.done():
                    self.ready.set_result(True)

        parent_msg_ig = data["parent_header"].get("msg_id", None)
        if parent_msg_ig is None:
            logger.warning("Parent message ID not found. %s", data)
            return

        execution = self._executions.get(parent_msg_ig)
        if not execution:
            return

        queue = execution.queue
        if data["msg_type"] == "error":
            logger.debug(
                f"Execution {parent_msg_ig} finished execution with error: {data['content']['ename']}: {data['content']['evalue']}"
            )

            if execution.errored:
                return

            execution.errored = True
            await queue.put(
                Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback="".join(data["content"]["traceback"]),
                )
            )

        elif data["msg_type"] == "stream":
            if data["content"]["name"] == "stdout":
                logger.debug(f"Execution {parent_msg_ig} received stdout")
                await queue.put(
                    Stdout(
                        text=data["content"]["text"], timestamp=data["header"]["date"]
                    )
                )

            elif data["content"]["name"] == "stderr":
                logger.debug(f"Execution {parent_msg_ig} received stderr")
                await queue.put(
                    Stderr(
                        text=data["content"]["text"], timestamp=data["header"]["date"]
                    )
                )

        elif data["msg_type"] in "display_data":
            result = Result(is_main_result=False, data=data["content"]["data"])
            logger.debug(
                f"Execution {parent_msg_ig} received display data with following formats: {result.formats()}"
            )
            await queue.put(result)

        elif data["msg_type"] == "execute_result":
            result = Result(is_main_result=True, data=data["content"]["data"])
            logger.debug(
                f"Execution {parent_msg_ig} received execution result with following formats: {result.formats()}"
            )
            await queue.put(result)

        elif data["msg_type"] == "status":
            if data["content"]["execution_state"] == "busy" and execution.in_background:
                logger.debug(f"Execution {parent_msg_ig} started execution")
                execution.input_accepted = True

            if data["content"]["execution_state"] == "idle":
                if execution.input_accepted:
                    logger.debug(f"Execution {parent_msg_ig} finished execution")
                    await queue.put(EndOfExecution())

            elif data["content"]["execution_state"] == "error":
                logger.debug(f"Execution {parent_msg_ig} finished execution with error")
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
                logger.debug(f"Execution {parent_msg_ig} finished execution with error")

                if execution.errored:
                    return

                execution.errored = True
                await queue.put(
                    Error(
                        name=data["content"].get("ename", ""),
                        value=data["content"].get("evalue", ""),
                        traceback="".join(data["content"].get("traceback", [])),
                    )
                )
            elif data["content"]["status"] == "abort":
                logger.debug(f"Execution {parent_msg_ig} was aborted")
                await queue.put(
                    Error(
                        name="ExecutionAborted",
                        value="Execution was aborted",
                        traceback="",
                    )
                )
                await queue.put(EndOfExecution())
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
        logger.debug(f"Closing WebSocket {self.context_id}")

        if self._ws is not None:
            await self._ws.close()

        self._receive_task.cancel()

        for execution in self._executions.values():
            execution.queue.put_nowait(UnexpectedEndOfExecution())
