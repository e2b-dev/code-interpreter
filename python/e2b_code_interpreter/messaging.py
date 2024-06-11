import json
import logging
import threading
import time
import uuid
from concurrent.futures import Future
from queue import Queue
from typing import Callable, Dict, Any, Optional

from e2b import ProcessMessage
from e2b.constants import TIMEOUT
from e2b.sandbox import TimeoutException
from e2b.sandbox.websocket_client import WebSocket
from e2b.utils.future import DeferredFuture

from e2b_code_interpreter.models import Execution, Result, Error

logger = logging.getLogger(__name__)


class CellExecution:
    """
    Represents the execution of a cell in the Jupyter kernel.
    It's an internal class used by JupyterKernelWebSocket.
    """

    input_accepted: bool = False

    on_stdout: Optional[Callable[[ProcessMessage], Any]] = None
    on_stderr: Optional[Callable[[ProcessMessage], Any]] = None
    on_result: Optional[Callable[[Result], Any]] = None

    def __init__(
        self,
        on_stdout: Optional[Callable[[ProcessMessage], Any]] = None,
        on_stderr: Optional[Callable[[ProcessMessage], Any]] = None,
        on_result: Optional[Callable[[Result], Any]] = None,
    ):
        self.partial_result = Execution()
        self.execution = Future()
        self.on_stdout = on_stdout
        self.on_stderr = on_stderr
        self.on_result = on_result


class JupyterKernelWebSocket:

    def __init__(self, url: str, session_id: str):
        self.url = url
        self.session_id = session_id
        self._cells: Dict[str, CellExecution] = {}
        self._waiting_for_replies: Dict[str, DeferredFuture] = {}
        self._queue_in = Queue()
        self._queue_out = Queue()
        self._stopped = threading.Event()

    def process_messages(self):
        while not self._stopped.is_set():
            if self._queue_out.empty():
                time.sleep(0.01)
                continue

            data = self._queue_out.get()
            logger.debug(f"WebSocket received message: {data}".strip())
            self._receive_message(json.loads(data))
            self._queue_out.task_done()

    def connect(self, timeout: float = TIMEOUT):
        started = threading.Event()

        threading.Thread(
            target=self.process_messages, daemon=True, name="e2b-process-messages"
        ).start()

        threading.Thread(
            target=WebSocket(
                url=self.url,
                queue_in=self._queue_in,
                queue_out=self._queue_out,
                started=started,
                stopped=self._stopped
            ).run,
            daemon=True,
            name="e2b-code-interpreter-websocket",
        ).start()

        logger.debug("WebSocket waiting to start")

        try:
            start_time = time.time()
            while (
                not started.is_set()
                and time.time() - start_time < timeout
                and not self._stopped.is_set()
            ):
                time.sleep(0.1)

            if not started.is_set():
                raise TimeoutException("WebSocket failed to start")
        except BaseException as e:
            self.close()
            raise Exception(f"WebSocket failed to start: {e}") from e

        logger.debug("WebSocket started")

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

    def send_execution_message(
        self,
        code: str,
        on_stdout: Optional[Callable[[ProcessMessage], Any]] = None,
        on_stderr: Optional[Callable[[ProcessMessage], Any]] = None,
        on_result: Optional[Callable[[Result], Any]] = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        logger.debug(f"Sending execution message: {message_id}")

        self._cells[message_id] = CellExecution(
            on_stdout=on_stdout,
            on_stderr=on_stderr,
            on_result=on_result,
        )
        request = self._get_execute_request(message_id, code)
        self._queue_in.put(request)
        return message_id

    def get_result(
        self, message_id: str, timeout: Optional[float] = TIMEOUT
    ) -> Execution:
        result = self._cells[message_id].execution.result(timeout=timeout)
        logger.debug(f"Got result for message: {message_id}")
        del self._cells[message_id]
        return result

    def _receive_message(self, data: dict):
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

        cell = self._cells.get(parent_msg_ig)
        if not cell:
            return

        execution = cell.partial_result

        if data["msg_type"] == "error":
            logger.debug(f"Cell {parent_msg_ig} finished execution with error")
            execution.error = Error(
                name=data["content"]["ename"],
                value=data["content"]["evalue"],
                traceback_raw=data["content"]["traceback"],
            )

        elif data["msg_type"] == "stream":
            if data["content"]["name"] == "stdout":
                execution.logs.stdout.append(data["content"]["text"])
                if cell.on_stdout:
                    cell.on_stdout(
                        ProcessMessage(
                            line=data["content"]["text"],
                            timestamp=time.time_ns(),
                        )
                    )

            elif data["content"]["name"] == "stderr":
                execution.logs.stderr.append(data["content"]["text"])
                if cell.on_stderr:
                    cell.on_stderr(
                        ProcessMessage(
                            line=data["content"]["text"],
                            error=True,
                            timestamp=time.time_ns(),
                        )
                    )

        elif data["msg_type"] in "display_data":
            result = Result(is_main_result=False, data=data["content"]["data"])
            execution.results.append(result)
            if cell.on_result:
                cell.on_result(result)
        elif data["msg_type"] == "execute_result":
            result = Result(is_main_result=True, data=data["content"]["data"])
            execution.results.append(result)
            if cell.on_result:
                cell.on_result(result)
        elif data["msg_type"] == "status":
            if data["content"]["execution_state"] == "idle":
                if cell.input_accepted:
                    logger.debug(f"Cell {parent_msg_ig} finished execution")
                    cell.execution.set_result(execution)

            elif data["content"]["execution_state"] == "error":
                logger.debug(f"Cell {parent_msg_ig} finished execution with error")
                execution.error = Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback_raw=data["content"]["traceback"],
                )
                cell.execution.set_result(execution)

        elif data["msg_type"] == "execute_reply":
            if data["content"]["status"] == "error":
                logger.debug(f"Cell {parent_msg_ig} finished execution with error")
                execution.error = Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback_raw=data["content"]["traceback"],
                )
            elif data["content"]["status"] == "ok":
                pass

        elif data["msg_type"] == "execute_input":
            logger.debug(f"Input accepted for {parent_msg_ig}")
            cell.partial_result.execution_count = data["content"]["execution_count"]
            cell.input_accepted = True
        else:
            logger.warning(f"[UNHANDLED MESSAGE TYPE]: {data['msg_type']}")

    def close(self):
        logger.debug("Closing WebSocket")
        self._stopped.set()

        for handler in self._waiting_for_replies.values():
            logger.debug(f"Cancelling waiting for execution result for {handler}")
            handler.cancel()
            del handler
