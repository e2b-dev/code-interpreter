from __future__ import annotations

import logging
import threading
import uuid
import requests

from concurrent.futures import Future
from typing import Any, Callable, List, Optional, Dict
from e2b import Sandbox

from e2b_code_interpreter.constants import TIMEOUT
from e2b_code_interpreter.messaging import CellMessage, JupyterKernelWebSocket
from e2b_code_interpreter.models import KernelException, Execution, Result

logger = logging.getLogger(__name__)


class CodeInterpreter(Sandbox):
    """
    E2B code interpreter sandbox extension.
    """

    default_template = "code-interpreter-stateful"

    def __init__(
        self,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        sandbox_id: Optional[str] = None,
        request_timeout: float = TIMEOUT,
    ):
        super().__init__(
            template=template,
            timeout=timeout,
            metadata=metadata,
            api_key=api_key,
            domain=domain,
            debug=debug,
            sandbox_id=sandbox_id,
            request_timeout=request_timeout,
        )
        self.notebook = JupyterExtension(self, request_timeout=request_timeout)

    def close(self):
        # Close all the websocket connections to the kernels
        self.notebook.close()

    def get_protocol(self, base_protocol: str = "http") -> str:
        """
        The function decides whether to use the secure or insecure protocol.

        :param base_protocol: Specify the specific protocol you want to use. Do not include the `s` in `https` or `wss`.
        :param secure: Specify whether you want to use the secure protocol or not.

        :return: Protocol for the connection to the sandbox
        """
        return base_protocol if self._connection_config.debug else f"{base_protocol}s"

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        super().__exit__(exc_type, exc_value, traceback)


class JupyterExtension:
    def __init__(self, sandbox: CodeInterpreter, request_timeout: float = TIMEOUT):
        self._sandbox = sandbox
        self._kernel_id_set = Future()
        self._start_connecting_to_default_kernel(request_timeout=request_timeout)
        self._connected_kernels: Dict[str, Future[JupyterKernelWebSocket]] = {}
        self._default_kernel_id: Optional[str] = None

    def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        on_stdout: Optional[Callable[[CellMessage], Any]] = None,
        on_stderr: Optional[Callable[[CellMessage], Any]] = None,
        on_result: Optional[Callable[[Result], Any]] = None,
        timeout: float = TIMEOUT,
        request_timeout: float = TIMEOUT,
    ) -> Execution:
        """
        Execute code in a notebook cell.

        :param code: Code to execute
        :param kernel_id: The ID of the kernel to execute the code on. If not provided, the default kernel is used.
        :param on_stdout: A callback function to handle standard output messages from the code execution.
        :param on_stderr: A callback function to handle standard error messages from the code execution.
        :param on_result: A callback function to handle the result and display calls of the code execution.
        :param timeout: Timeout for the call

        :return: Result of the execution
        """
        kernel_id = kernel_id or self.default_kernel_id
        ws_future = self._connected_kernels.get(kernel_id)

        logger.debug(f"Executing code in kernel {kernel_id}")

        if ws_future:
            logger.debug(f"Using existing websocket connection to kernel {kernel_id}")
            ws = ws_future.result(timeout=timeout)
        else:
            logger.debug(f"Creating new websocket connection to kernel {kernel_id}")
            ws = self._connect_to_kernel_ws(
                kernel_id,
                None,
                request_timeout=request_timeout,
            )

        message_id = ws.send_execution_message(code, on_stdout, on_stderr, on_result)
        logger.debug(
            f"Sent execution message to kernel {kernel_id}, message_id: {message_id}"
        )

        result = ws.get_result(message_id, timeout=timeout)
        logger.debug(
            f"Received result from kernel {kernel_id}, message_id: {message_id}, result: {result}"
        )

        return result

    @property
    def default_kernel_id(self) -> str:
        """
        Get the default kernel id

        :return: Default kernel id
        """
        if not self._default_kernel_id:
            logger.debug("Waiting for default kernel id")
            self._default_kernel_id = self._kernel_id_set.result()

        return self._default_kernel_id

    def create_kernel(
        self,
        cwd: str = "/home/user",
        kernel_name: Optional[str] = None,
        request_timeout: Optional[float] = TIMEOUT,
    ) -> str:
        """
        Creates a new kernel, this can be useful if you want to have multiple independent code execution environments.

        The kernel can be optionally configured to start in a specific working directory and/or
        with a specific kernel name. If no kernel name is provided, the default kernel will be used.
        Once the kernel is created, this method establishes a WebSocket connection to the new kernel for
        real-time communication.

        :param cwd: Sets the current working directory for the kernel. Defaults to "/home/user".
        :param kernel_name:
            Specifies which kernel should be used, useful if you have multiple kernel types.
            If not provided, the default kernel will be used.
        :param request_timeout: Timeout for the kernel creation request.
        :return: Kernel id of the created kernel
        """
        kernel_name = kernel_name or "python3"

        data = {
            "path": str(uuid.uuid4()),
            "kernel": {"name": kernel_name},
            "type": "notebook",
            "name": str(uuid.uuid4()),
        }
        logger.debug(f"Creating kernel with data: {data}")

        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_host(8888)}/api/sessions",
            json=data,
            timeout=request_timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to create kernel: {response.text}")

        session_data = response.json()
        session_id = session_data["id"]
        kernel_id = session_data["kernel"]["id"]

        response = requests.patch(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_host(8888)}/api/sessions/{session_id}",
            json={"path": cwd},
            timeout=request_timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to create kernel: {response.text}")

        logger.debug(f"Created kernel {kernel_id}")

        threading.Thread(
            target=self._connect_to_kernel_ws,
            args=(kernel_id, session_id, request_timeout),
        ).start()
        return kernel_id

    def restart_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = TIMEOUT,
    ) -> None:
        """
        Restarts an existing Jupyter kernel. This can be useful to reset the kernel's state or to recover from errors.

        :param kernel_id: The unique identifier of the kernel to restart. If not provided, the default kernel is restarted.
        :param timeout: The timeout in milliseconds for the kernel restart request.
        """
        kernel_id = kernel_id or self.default_kernel_id
        logger.debug(f"Restarting kernel {kernel_id}")

        self._connected_kernels[kernel_id].result().close()
        del self._connected_kernels[kernel_id]
        logger.debug(f"Closed websocket connection to kernel {kernel_id}")

        response = requests.post(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_host(8888)}/api/kernels/{kernel_id}/restart",
            timeout=request_timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to restart kernel {kernel_id}")

        logger.debug(f"Restarted kernel {kernel_id}")

        threading.Thread(
            target=self._connect_to_kernel_ws, args=(kernel_id, None, request_timeout)
        ).start()

    def shutdown_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = TIMEOUT,
    ) -> None:
        """
        Shuts down an existing Jupyter kernel. This method is used to gracefully terminate a kernel's process.

        :param kernel_id: The unique identifier of the kernel to shutdown. If not provided, the default kernel is shutdown.
        :param timeout: The timeout for the kernel shutdown request.
        """
        kernel_id = kernel_id or self.default_kernel_id
        logger.debug(f"Shutting down kernel {kernel_id}")

        self._connected_kernels[kernel_id].result().close()
        del self._connected_kernels[kernel_id]
        logger.debug(f"Closed websocket connection to kernel {kernel_id}")

        response = requests.delete(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_host(8888)}/api/kernels/{kernel_id}",
            timeout=request_timeout,
        )
        if not response.ok:
            raise KernelException(f"Failed to shutdown kernel {kernel_id}")

        logger.debug(f"Shutdown kernel {kernel_id}")

    def list_kernels(self, request_timeout: Optional[float] = TIMEOUT) -> List[str]:
        """
        Lists all available Jupyter kernels.

        This method fetches a list of all currently available Jupyter kernels from the server. It can be used
        to retrieve the IDs of all kernels that are currently running or available for connection.

        :param timeout: The timeout for the kernel list request.
        :return: List of kernel ids
        """
        response = requests.get(
            f"{self._sandbox.get_protocol()}://{self._sandbox.get_host(8888)}/api/kernels",
            timeout=request_timeout,
        )

        if not response.ok:
            raise KernelException(f"Failed to list kernels: {response.text}")

        return [kernel["id"] for kernel in response.json()]

    def close(self):
        """
        Close all the websocket connections to the kernels. It doesn't shutdown the kernels.
        """
        logger.debug("Closing all websocket connections")
        for ws in self._connected_kernels.values():
            ws.result().close()

    def _connect_to_kernel_ws(
        self,
        kernel_id: str,
        session_id: Optional[str],
        request_timeout: float = TIMEOUT,
    ) -> JupyterKernelWebSocket:
        """
        Establishes a WebSocket connection to a specified Jupyter kernel.

        :param kernel_id: Kernel id
        :param timeout: The timeout for the kernel connection request.

        :return: Websocket connection
        """
        logger.debug(f"Connecting to kernel's ({kernel_id}) websocket")
        future = Future()
        self._connected_kernels[kernel_id] = future

        session_id = session_id or str(uuid.uuid4())
        ws = JupyterKernelWebSocket(
            url=f"{self._sandbox.get_protocol('ws')}://{self._sandbox.get_host(8888)}/api/kernels/{kernel_id}/channels",
            session_id=session_id,
        )

        ws.connect(timeout=request_timeout)
        logger.debug(f"Connected to kernel's ({kernel_id}) websocket.")

        future.set_result(ws)
        return ws

    def _start_connecting_to_default_kernel(
        self, request_timeout: float = TIMEOUT
    ) -> None:
        """
        Start connecting to the default kernel in a separate thread to avoid blocking the main thread.
        :param timeout: Timeout for the call
        """
        logger.debug("Starting to connect to the default kernel")

        def setup_default_kernel():
            kernel_id = self._sandbox.files.read(
                "/root/.jupyter/kernel_id", request_timeout=request_timeout
            )

            if kernel_id is None and not self._sandbox.is_running(
                request_timeout=request_timeout
            ):
                return

            kernel_id = kernel_id.strip()

            logger.debug(f"Default kernel id: {kernel_id}")
            self._connect_to_kernel_ws(kernel_id, None, request_timeout=request_timeout)
            self._kernel_id_set.set_result(kernel_id)

        threading.Thread(target=setup_default_kernel).start()
