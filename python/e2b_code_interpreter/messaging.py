import json
import threading
import time
import uuid
from concurrent.futures import Future
from queue import Queue
from typing import Callable, Dict, List, Any, Optional

from e2b import ProcessMessage
from e2b.constants import TIMEOUT
from e2b.sandbox import TimeoutException
from e2b.sandbox.websocket_client import WebSocket
from e2b.utils.future import DeferredFuture
from pydantic import ConfigDict, PrivateAttr, BaseModel

from e2b_code_interpreter.models import Result, Error


class Cell:
    input_accepted: bool = False
    on_stdout: Optional[Callable[[Any], None]] = None
    on_stderr: Optional[Callable[[Any], None]] = None

    def __init__(self, on_stdout: Optional[Callable[[Any], None]] = None, on_stderr: Optional[Callable[[Any], None]] = None):
        self.partial_result = Result()
        self.result = Future()
        self.on_stdout = on_stdout
        self.on_stderr = on_stderr


class JupyterKernelWebSocket(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str

    _cells: Dict[str, Cell] = {}
    _waiting_for_replies: Dict[str, DeferredFuture] = PrivateAttr(default_factory=dict)
    _queue_in: Queue = PrivateAttr(default_factory=Queue)
    _queue_out: Queue = PrivateAttr(default_factory=Queue)
    _process_cleanup: List[Callable[[], Any]] = PrivateAttr(default_factory=list)
    _closed: bool = PrivateAttr(default=False)

    def process_messages(self):
        while True:
            data = self._queue_out.get()

            # logger.debug(f"WebSocket received message: {data}".strip())
            self._receive_message(json.loads(data))
            self._queue_out.task_done()

    def connect(self, timeout: float = TIMEOUT):
        started = threading.Event()
        stopped = threading.Event()
        self._process_cleanup.append(stopped.set)

        threading.Thread(
            target=self.process_messages, daemon=True, name="e2b-process-messages"
        ).start()

        threading.Thread(
            target=WebSocket(
                url=self.url,
                queue_in=self._queue_in,
                queue_out=self._queue_out,
                started=started,
                stopped=stopped,
            ).run,
            daemon=True,
            name="e2b-code-interpreter-websocket",
        ).start()

        # logger.info("WebSocket waiting to start")

        try:
            start_time = time.time()
            while (
                not started.is_set()
                and time.time() - start_time < timeout
                and not self._closed
            ):
                time.sleep(0.1)

            if not started.is_set():
                # logger.error("WebSocket failed to start")
                raise TimeoutException("WebSocket failed to start")
        except BaseException as e:
            self.close()
            raise Exception(f"WebSocket failed to start: {e}") from e

        # logger.info("WebSocket started")

    @staticmethod
    def _get_execute_request(msg_id: str, code: str) -> str:
        return json.dumps({
            "header": {
                "msg_id": msg_id,
                "username": "e2b",
                "session": str(uuid.uuid4()),
                "msg_type": "execute_request",
                "version": "5.3",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": False,
            },
        })

    def send_execution_message(
        self,
        code: str,
        on_stdout: Optional[Callable[[Any], None]] = None,
        on_stderr: Optional[Callable[[Any], None]] = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        self._cells[message_id] = Cell(
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )
        request = self._get_execute_request(message_id, code)
        self._queue_in.put(request)
        return message_id

    def get_result(self, message_id: str, timeout: Optional[float] = TIMEOUT) -> Result:
        result = self._cells[message_id].result.result(timeout=timeout)
        del self._cells[message_id]
        return result

    def _receive_message(self, data: dict):
        parent_msg_ig = data["parent_header"]["msg_id"]
        cell = self._cells.get(parent_msg_ig)
        if not cell:
            return

        result = cell.partial_result

        if data["msg_type"] == "error":
            result.error = Error(
                name=data["content"]["ename"],
                value=data["content"]["evalue"],
                traceback=data["content"]["traceback"],
            )

        elif data["msg_type"] == "stream":
            if data["content"]["name"] == "stdout":
                result.stdout.append(data["content"]["text"])
                if cell.on_stdout:
                    cell.on_stdout(
                        ProcessMessage(
                            line=data["content"]["text"],
                            timestamp=time.time_ns(),
                        )
                    )

            elif data["content"]["name"] == "stderr":
                result.stderr.append(data["content"]["text"])
                if cell.on_stderr:
                    cell.on_stderr(
                        ProcessMessage(
                            line=data["content"]["text"],
                            error=True,
                            timestamp=time.time_ns(),
                        )
                    )

        elif data["msg_type"] == "display_data":
            result.display_data.append(data["content"]["data"])

        elif data["msg_type"] == "execute_result":
            result.output = data["content"]["data"]["text/plain"]

        elif data["msg_type"] == "status":
            if data["content"]["execution_state"] == "idle":
                if cell.input_accepted:
                    cell.result.set_result(result)

            elif data["content"]["execution_state"] == "error":
                result.error = Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback=data["content"]["traceback"],
                )
                cell.result.set_result(result)

        elif data["msg_type"] == "execute_reply":
            if data["content"]["status"] == "error":
                result.error = Error(
                    name=data["content"]["ename"],
                    value=data["content"]["evalue"],
                    traceback=data["content"]["traceback"],
                )
            elif data["content"]["status"] == "ok":
                pass

        elif data["msg_type"] == "execute_input":
            cell.input_accepted = True
        else:
            print("[UNHANDLED MESSAGE TYPE]:", data["msg_type"])

    def close(self):
        self._closed = True

        for cancel in self._process_cleanup:
            cancel()

        self._process_cleanup.clear()

        for handler in self._waiting_for_replies.values():
            handler.cancel()
            del handler
