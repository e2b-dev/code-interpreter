import threading
from concurrent.futures import Future
from typing import Any, Callable, List, Optional, Dict

import requests
from e2b import EnvVars, ProcessMessage, Sandbox
from e2b.constants import TIMEOUT

from e2b_code_interpreter.messaging import JupyterKernelWebSocket
from e2b_code_interpreter.models import KernelException, Result


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
        # Close all the websocket connections when the interpreter is closed
        self._process_cleanup.append(self.notebook.close)


class JupyterExtension:
    _default_kernel_id: Optional[str] = None
    _connected_kernels: Dict[str, JupyterKernelWebSocket] = {}

    def __init__(self, sandbox: CodeInterpreter):
        self._sandbox = sandbox
        self._kernel_id_set = Future()
        self._start_connecting_to_default_kernel()

    def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        on_stdout: Optional[Callable[[ProcessMessage], Any]] = None,
        on_stderr: Optional[Callable[[ProcessMessage], Any]] = None,
    ) -> Result:
        """
        Execute code in a notebook cell.
        :param code: Code to execute
        :param kernel_id: Kernel id to use, if not provided the default kernel will be used
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :return: Result of the execution
        """
        kernel_id = kernel_id or self.default_kernel_id
        ws = self._connected_kernels.get(kernel_id)

        if not ws:
            ws = JupyterKernelWebSocket(
                url=f"{self._sandbox.get_protocol('ws')}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}/channels",
            )
            self._connected_kernels[kernel_id] = ws
            ws.connect()

        session_id = ws.send_execution_message(code, on_stdout, on_stderr)

        result = ws.get_result(session_id)
        return result

    @property
    def default_kernel_id(self) -> str:
        """
        Get the default kernel id
        :return: Default kernel id
        """
        if not self._default_kernel_id:
            self._default_kernel_id = self._kernel_id_set.result()

        return self._default_kernel_id

    def create_kernel(
            self,
            cwd: str = "/home/user",
            kernel_name: Optional[str] = None,
            timeout: Optional[float] = TIMEOUT
    ) -> str:
        """
        Create a new kernel, this can be useful if you want to have multiple independent code execution environments.
        :param cwd: Sets the current working directory for the kernel
        :param kernel_name:
            Specifies which kernel should be used, useful if you have multiple kernel types.
            If not provided, the default kernel will be used - "python3".
        :param timeout: Sets timeout for the call
        :return: Kernel id of the created kernel
        """
        data = {"cwd": cwd}
        if kernel_name:
            data["kernel_name"] = kernel_name

        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels",
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to create kernel: {response.text}")

        kernel_id = response.json()["id"]

        threading.Thread(target=self._connect_to_kernel_ws, args=kernel_id).start()
        return kernel_id

    def restart_kernel(
        self, kernel_id: Optional[str] = None, timeout: Optional[float] = TIMEOUT
    ) -> None:
        """
        Restart a kernel
        :param kernel_id:
        :param timeout:
        :return:
        """
        kernel_id = kernel_id or self.default_kernel_id

        self._connected_kernels[kernel_id].close()
        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}/restart",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to restart kernel {kernel_id}")

        threading.Thread(target=self._connect_to_kernel_ws, args=kernel_id).start()

    def shutdown_kernel(
        self, kernel_id: Optional[str] = None, timeout: Optional[float] = TIMEOUT
    ) -> None:
        """
        Shutdown a kernel
        :param kernel_id: Kernel id to shutdown
        :param timeout: Timeout for the call
        """
        kernel_id = kernel_id or self.default_kernel_id

        self._connected_kernels[kernel_id].close()
        response = requests.delete(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to shutdown kernel {kernel_id}")

    def list_kernels(self, timeout: Optional[float] = TIMEOUT) -> List[str]:
        """
        List all the kernels
        :param timeout: Timeout for the call
        :return: List of kernel ids
        """
        response = requests.get(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_hostname(8888)}/api/kernels",
            timeout=timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to list kernels: {response.text}")
        return [kernel["id"] for kernel in response.json()]

    def close(self):
        """
        Close all the websocket connections to the kernels. It doesn't shutdown the kernels.
        :return:
        """
        for ws in self._connected_kernels.values():
            ws.close()

    def _connect_to_kernel_ws(self, kernel_id: str) -> None:
        ws = JupyterKernelWebSocket(
            url=f"{self._sandbox.get_protocol('ws')}://{self._sandbox.get_hostname(8888)}/api/kernels/{kernel_id}/channels",
        )
        ws.connect()
        self._connected_kernels[kernel_id] = ws

    def _start_connecting_to_default_kernel(self, timeout: Optional[float] = TIMEOUT) -> None:
        def setup_default_kernel():
            kernel_id = self._sandbox.filesystem.read("/root/.jupyter/kernel_id", timeout=timeout).strip()
            self._connect_to_kernel_ws(kernel_id)
            self._kernel_id_set.set_result(kernel_id)

        threading.Thread(target=setup_default_kernel).start()
