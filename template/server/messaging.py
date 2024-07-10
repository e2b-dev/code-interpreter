import json
import logging
import uuid
import asyncio
import random
from asyncio import Future, Queue

from typing import Callable, Dict, Any, AsyncIterator, List, AsyncIterable

from api.models.error import Error
from api.models.logs import Stdout, Stderr
from api.models.result import Result
from api.models.output import EndOfExecution, NumberOfExecutions, OutputType
from websockets.legacy.client import WebSocketClientProtocol, Connect
from websockets.exceptions import ConnectionClosed


TIMEOUT = 60


logger = logging.getLogger(__name__)


class Execution:
    def __init__(self):
        self.queue = Queue()
        self.input_accepted = False


class JupyterKernelWebSocket:
    _ws: WebSocketClientProtocol = None

    def __init__(self, url: str, session_id: str):
        self.url = url
        self.session_id = session_id
        self._executions: Dict[str, Execution] = {}
        self._process_cleanup: List[Callable[[], Any]] = []
        self._waiting_for_replies: Dict[str, Future] = {}
        self._stopped = Future()
        self.started = Future()

    async def connect(self, timeout: float = TIMEOUT):
        logger.debug(f"WebSocket connecting to {self.url}")

        ws_logger = logger.getChild("websockets.client")
        ws_logger.setLevel(logging.ERROR)

        websocket_connector = E2BConnect(
            self.url,
            max_size=None,
            max_queue=None,
            logger=ws_logger,
        )

        websocket_connector.BACKOFF_MIN = 1
        websocket_connector.BACKOFF_FACTOR = 1
        websocket_connector.BACKOFF_INITIAL = 0.2  # type: ignore

        async for websocket in websocket_connector:
            try:
                self._ws = websocket
                self.started.set_result(None)

                logger.info(f"WebSocket connected to {self.url}")

                receive_task = asyncio.create_task(
                    self._receive_message(), name="receive_message"
                )
                self._process_cleanup.append(receive_task.cancel)

                while not self._stopped.done():
                    await asyncio.sleep(0)

                logger.info("WebSocket stopped")
                break
            except ConnectionClosed:
                logger.warning("WebSocket disconnected, it will try to reconnect")
                if self._stopped.done():
                    break

    def _get_execute_request(self, msg_id: str, code: str) -> str:
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

    async def execute(self, code: str) -> AsyncIterable:
        message_id = str(uuid.uuid4())
        logger.debug(f"Sending execution for code ({message_id}): {code}")

        self._executions[message_id] = Execution()
        request = self._get_execute_request(message_id, code)

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
        try:
            if not self._ws:
                logger.error("No WebSocket connection")
                return
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
            await queue.put(Error(
                name=data["content"]["ename"],
                value=data["content"]["evalue"],
                traceback="".join(data["content"]["traceback"]),
            ))

        elif data["msg_type"] == "stream":
            if data["content"]["name"] == "stdout":
                await queue.put(Stdout(text=data['content']['text'], timestamp=data['header']['date']))

            elif data["content"]["name"] == "stderr":
                await queue.put(Stderr(text=data['content']['text'], timestamp=data['header']['date']))

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
                await queue.put(Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback="".join(data["content"]["traceback"]),
                ))
                await queue.put(EndOfExecution())

        elif data["msg_type"] == "execute_reply":
            if data["content"]["status"] == "error":
                logger.debug(f"Cell {parent_msg_ig} finished execution with error")
                await queue.put(Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback=''.join(data["content"]["traceback"]),
                ))
            elif data["content"]["status"] == "ok":
                pass

        elif data["msg_type"] == "execute_input":
            logger.debug(f"Input accepted for {parent_msg_ig}")
            await queue.put(NumberOfExecutions(execution_count=data["content"]["execution_count"]))
            execution.input_accepted = True
        else:
            logger.warning(f"[UNHANDLED MESSAGE TYPE]: {data['msg_type']}")

    async def close(self):
        logger.debug("Closing WebSocket")
        self._stopped.set_result(None)
        await self._ws.close()

        for handler in self._waiting_for_replies.values():
            logger.debug(f"Cancelling waiting for execution result for {handler}")
            handler.cancel()
            del handler


class E2BConnect(Connect):
    async def __aiter__(self) -> AsyncIterator[WebSocketClientProtocol]:
        retries = 0
        max_retries = 12
        backoff_delay = 0.1
        while True:
            try:
                async with self as protocol:
                    yield protocol
            except Exception:
                retries += 1
                if retries >= max_retries:
                    raise Exception("Failed to connect to the server")
                # Add a random initial delay between 0 and 5 seconds.
                # See 7.2.3. Recovering from Abnormal Closure in RFC 6544.
                if backoff_delay == 0.1:
                    initial_delay = random.random()
                    self.logger.info(
                        "! connect failed; reconnecting in %.1f seconds",
                        initial_delay,
                        exc_info=True,
                    )
                    await asyncio.sleep(initial_delay)
                else:
                    self.logger.info(
                        "! connect failed again; retrying in %d seconds",
                        int(backoff_delay),
                        exc_info=True,
                    )
                    await asyncio.sleep(int(backoff_delay))
                # Increase delay with truncated exponential backoff.
                if retries > 4:
                    backoff_delay = backoff_delay * 1.2
                backoff_delay = min(backoff_delay, 10)
                continue
            else:
                # Connection succeeded - reset backoff delay
                backoff_delay = 0.1
