import json
import threading
import time
import uuid
from concurrent.futures import Future
from typing import Any, Callable, List, Optional

import requests
from e2b import EnvVars, ProcessMessage, Sandbox
from e2b.constants import TIMEOUT
from websocket import create_connection

from e2b_code_interpreter.models import Error, KernelException, Result


class CodeInterpreter(Sandbox):
    template = "code-interpreter-stateful"

    def __init__(
        self,
        template: Optional[str] = None,
        api_key: Optional[str] = None,
        cwd: Optional[str] = None,
        env_vars: Optional[EnvVars] = None,
        timeout: Optional[float] = TIMEOUT,
        on_stdout: Optional[Callable[[ProcessMessage], Any]] = None,
        on_stderr: Optional[Callable[[ProcessMessage], Any]] = None,
        on_exit: Optional[Callable[[int], Any]] = None,
        **kwargs,
    ):
        super().__init__(
            template=template or self.template,
            api_key=api_key,
            cwd=cwd,
            env_vars=env_vars,
            timeout=timeout,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
            on_exit=on_exit,
            **kwargs,
        )
        self.notebook = JupyterExtension(self)


class JupyterExtension:
    _default_kernel_id: Optional[str] = None

    def __init__(self, sandbox: CodeInterpreter):
        self._sandbox = sandbox
        self._kernel_id_set = Future()
        self._set_default_kernel_id()

    def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        on_stdout: Optional[Callable[[ProcessMessage], Any]] = None,
        on_stderr: Optional[Callable[[ProcessMessage], Any]] = None,
    ) -> Result:
        kernel_id = kernel_id or self.default_kernel_id
        ws = self._connect_kernel(kernel_id)
        ws.send(json.dumps(self._send_execute_request(code)))
        result = self._wait_for_result(ws, on_stdout, on_stderr)

        ws.close()

        return result

    @property
    def default_kernel_id(self) -> str:
        if not self._default_kernel_id:
            self._default_kernel_id = self._kernel_id_set.result()

        return self._default_kernel_id

    def create_kernel(self, timeout: Optional[float] = TIMEOUT) -> str:
        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to create kernel: {response.text}")
        return response.json()["id"]

    def restart_kernel(
        self, kernel_id: Optional[str] = None, timeout: Optional[float] = TIMEOUT
    ) -> None:
        kernel_id = kernel_id or self.default_kernel_id
        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}/restart",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to restart kernel {kernel_id}")

    def shutdown_kernel(
        self, kernel_id: Optional[str] = None, timeout: Optional[float] = TIMEOUT
    ) -> None:
        kernel_id = kernel_id or self.default_kernel_id

        response = requests.delete(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to shutdown kernel {kernel_id}")

    def list_kernels(self, timeout: Optional[float] = TIMEOUT) -> List[str]:
        response = requests.get(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to list kernels: {response.text}")
        return [kernel["id"] for kernel in response.json()]

    def _set_default_kernel_id(self, timeout: Optional[float] = TIMEOUT) -> None:
        def set_kernel_id():
            self._kernel_id_set.set_result(
                self._sandbox.filesystem.read("/root/.jupyter/kernel_id", timeout=timeout).strip()
            )

        threading.Thread(target=set_kernel_id).start()

    def _connect_kernel(self, kernel_id: str, timeout: Optional[float] = TIMEOUT):
        return create_connection(
            f"{self._sandbox.get_protocol('ws')}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}/channels",
            timeout=timeout,
        )

    @staticmethod
    def _send_execute_request(code: str) -> dict:
        msg_id = str(uuid.uuid4())
        session = str(uuid.uuid4())

        return {
            "header": {
                "msg_id": msg_id,
                "username": "e2b",
                "session": session,
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
        }

    @staticmethod
    def _wait_for_result(
        ws,
        on_stdout: Optional[Callable[[ProcessMessage], Any]],
        on_stderr: Optional[Callable[[ProcessMessage], Any]],
    ) -> Result:
        result = Result()
        input_accepted = False

        while True:
            response = json.loads(ws.recv())
            if response["msg_type"] == "error":
                result.error = Error(
                    name=response["content"]["ename"],
                    value=response["content"]["evalue"],
                    traceback=response["content"]["traceback"],
                )

            elif response["msg_type"] == "stream":
                if response["content"]["name"] == "stdout":
                    result.stdout.append(response["content"]["text"])
                    if on_stdout:
                        on_stdout(
                            ProcessMessage(
                                line=response["content"]["text"],
                                timestamp=time.time_ns(),
                            )
                        )

                elif response["content"]["name"] == "stderr":
                    result.stderr.append(response["content"]["text"])
                    if on_stderr:
                        on_stderr(
                            ProcessMessage(
                                line=response["content"]["text"],
                                error=True,
                                timestamp=time.time_ns(),
                            )
                        )

            elif response["msg_type"] == "display_data":
                result.display_data.append(response["content"]["data"])

            elif response["msg_type"] == "execute_result":
                result.output = response["content"]["data"]["text/plain"]

            elif response["msg_type"] == "status":
                if response["content"]["execution_state"] == "idle":
                    if input_accepted:
                        break
                elif response["content"]["execution_state"] == "error":
                    result.error = Error(
                        name=response["content"]["ename"],
                        value=response["content"]["evalue"],
                        traceback=response["content"]["traceback"],
                    )
                    break

            elif response["msg_type"] == "execute_reply":
                if response["content"]["status"] == "error":
                    result.error = Error(
                        name=response["content"]["ename"],
                        value=response["content"]["evalue"],
                        traceback=response["content"]["traceback"],
                    )
                elif response["content"]["status"] == "ok":
                    pass

            elif response["msg_type"] == "execute_input":
                input_accepted = True
            else:
                print("[UNHANDLED MESSAGE TYPE]:", response["msg_type"])
        return result
