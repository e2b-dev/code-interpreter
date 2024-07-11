import logging

from typing import Optional, List
from httpx import AsyncHTTPTransport, AsyncClient

from e2b import AsyncSandbox, ConnectionConfig

from e2b_code_interpreter.constants import DEFAULT_TEMPLATE, JUPYTER_PORT
from e2b_code_interpreter.models import (
    Execution,
    Kernel,
    Result,
    parse_output,
    OutputHandler,
    OutputMessage,
)

logger = logging.getLogger(__name__)


class JupyterExtension:
    _exec_timeout = 300

    @property
    def _client(self) -> AsyncClient:
        return AsyncClient(transport=self._transport)

    def __init__(
        self,
        url: str,
        transport: AsyncHTTPTransport,
        connection_config: ConnectionConfig,
    ):
        self._url = url
        self._transport = transport
        self._connection_config = connection_config

    async def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        logger.debug(f"Executing code {code}")

        timeout = None if timeout == 0 else (timeout or self._exec_timeout)
        request_timeout = request_timeout or self._connection_config.request_timeout

        async with self._client.stream(
            "POST",
            self._url,
            json={
                "code": code,
                "kernel_id": kernel_id,
            },
            timeout=(request_timeout, timeout, request_timeout, request_timeout),
        ) as response:

            response.raise_for_status()

            execution = Execution()

            async for line in response.aiter_lines():
                parse_output(execution, line, on_stdout, on_stderr, on_result)

            return execution

    async def create_kernel(
        self,
        cwd: Optional[str] = "/home/user",
        kernel_name: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> str:
        logger.debug(f"Creating new kernel: {kernel_name}")

        response = await self._client.post(
            f"{self._url}/contexts",
            json={
                "language": kernel_name,
                "cwd": cwd,
            },
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

        return response.json().kernel_id

    async def restart_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Restarting kernel: {kernel_id}")

        response = await self._client.post(
            f"{self._url}/contexts/{kernel_id}/restart",
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

    async def shutdown_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Creating new kernel for language: {kernel_id}")

        response = await self._client.request(
            method="DELETE",
            url=f"{self._url}/contexts/{kernel_id}",
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

    async def list_kernels(
        self,
        request_timeout: Optional[float] = None,
    ) -> List[Kernel]:
        """
        Lists all available Jupyter kernels.

        This method fetches a list of all currently available Jupyter kernels from the server. It can be used
        to retrieve the IDs of all kernels that are currently running or available for connection.

        :param timeout: The timeout for the kernel list request.
        :return: List of kernel ids
        """
        response = await self._client.get(
            f"{self._url}/contexts",
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

        return [Kernel(k.kernel_id, k.name) for k in response.json()]


class AsyncCodeInterpreter(AsyncSandbox):
    default_template = DEFAULT_TEMPLATE
    _jupyter_port = JUPYTER_PORT

    @property
    def notebook(self) -> JupyterExtension:
        return self._notebook

    def __init__(self, sandbox_id: str, connection_config: ConnectionConfig):
        super().__init__(sandbox_id, connection_config)

        jupyter_url = f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(self._jupyter_port)}/execute"

        self._notebook = JupyterExtension(
            jupyter_url,
            self._transport,
            self.connection_config,
        )
