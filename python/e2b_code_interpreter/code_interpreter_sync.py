import logging

from typing import Optional, Dict, List
from httpx import HTTPTransport, Client
from e2b import Sandbox, Stderr, Stdout, ConnectionConfig

from e2b_code_interpreter.constants import DEFAULT_TEMPLATE, JUPYTER_PORT
from e2b_code_interpreter.models import Execution, Result, parse_output, OutputHandler

logger = logging.getLogger(__name__)


class JupyterExtension:
    _exec_timeout = 300

    @property
    def _client(self) -> Client:
        return Client(transport=self._transport)

    def __init__(
        self,
        url: str,
        transport: HTTPTransport,
        connection_config: ConnectionConfig,
    ):
        self._url = url
        self._transport = transport
        self._connection_config = connection_config

    def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        language: Optional[str] = None,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        logger.debug(f"Executing code {code} for language {language}")

        timeout = None if timeout == 0 else (timeout or self._exec_timeout)
        request_timeout = request_timeout or self._connection_config.request_timeout
        execution = Execution()

        with self._client.stream(
            "POST",
            f"{self._url}/execute",
            json={
                "code": code,
                # "language": language,
                "kernel_id": kernel_id,
            },
            timeout=(request_timeout, timeout, request_timeout, request_timeout),
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                parse_output(
                    execution,
                    line,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                    on_result=on_result,
                )

        return execution

    def create_kernel(
        self,
        cwd: Optional[str] = "/home/user",
        kernel_name: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> str:
        logger.debug(f"Creating new kernel: {kernel_name}")

        response = self._client.post(
            f"{self._url}/contexts",
            json={
                "language": kernel_name,
                "cwd": cwd,
            },
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

        return response.json().kernel_id

    def shutdown_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Creating new kernel for language: {kernel_id}")

        response = self._client.request(
            method="DELETE",
            url=f"{self._url}/contexts",
            json={"kernel_id": kernel_id},
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

    def restart_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Creating new kernel for language: {kernel_id}")

        response = self._client.post(
            f"{self._url}/contexts/restart",
            json={"kernel_id": kernel_id},
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

    def list_kernels(
        self,
        request_timeout: Optional[float] = None,
    ) -> List[str]:
        """
        Lists all available Jupyter kernels.

        This method fetches a list of all currently available Jupyter kernels from the server. It can be used
        to retrieve the IDs of all kernels that are currently running or available for connection.

        :param timeout: The timeout for the kernel list request.
        :return: List of kernel ids
        """
        response = self._client.get(
            f"{self._url}/contexts",
            timeout=request_timeout or self._connection_config.request_timeout,
        )
        response.raise_for_status()

        return [k.kernel_id for k in response.json()]


class CodeInterpreter(Sandbox):
    default_template = DEFAULT_TEMPLATE
    _jupyter_port = JUPYTER_PORT

    @property
    def notebook(self) -> JupyterExtension:
        return self._notebook

    def __init__(
        self,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        sandbox_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
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

        jupyter_url = f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(self._jupyter_port)}"
        self._notebook = JupyterExtension(
            jupyter_url,
            self._transport,
            self.connection_config,
        )
