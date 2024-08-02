import logging
import httpx

from typing import Optional, Dict, List
from httpx import HTTPTransport, Client
from e2b import Sandbox, ConnectionConfig

from e2b_code_interpreter.constants import (
    DEFAULT_KERNEL_ID,
    DEFAULT_TEMPLATE,
    JUPYTER_PORT,
)
from e2b_code_interpreter.models import (
    Execution,
    Kernel,
    Result,
    extract_exception,
    parse_output,
    OutputHandler,
    OutputMessage,
)
from e2b_code_interpreter.exceptions import (
    format_execution_timeout_error,
    format_request_timeout_error,
)

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
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        logger.debug(f"Executing code {code}")

        timeout = None if timeout == 0 else (timeout or self._exec_timeout)
        request_timeout = request_timeout or self._connection_config.request_timeout

        try:
            with self._client.stream(
                "POST",
                f"{self._url}/execute",
                json={
                    "code": code,
                    "context_id": kernel_id,
                },
                timeout=(request_timeout, timeout, request_timeout, request_timeout),
            ) as response:
                err = extract_exception(response)
                if err:
                    raise err

                execution = Execution()

                for line in response.iter_lines():
                    parse_output(
                        execution,
                        line,
                        on_stdout=on_stdout,
                        on_stderr=on_stderr,
                        on_result=on_result,
                    )

                return execution
        except httpx.ReadTimeout:
            raise format_execution_timeout_error()
        except httpx.TimeoutException:
            raise format_request_timeout_error()

    def create_kernel(
        self,
        cwd: Optional[str] = None,
        kernel_name: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> str:
        logger.debug(f"Creating new kernel: {kernel_name}")

        data = {}
        if kernel_name:
            data["name"] = kernel_name
        if cwd:
            data["cwd"] = cwd

        try:
            response = self._client.post(
                f"{self._url}/contexts",
                json=data,
                timeout=request_timeout or self._connection_config.request_timeout,
            )

            err = extract_exception(response)
            if err:
                raise err

            data = response.json()
            return data["id"]
        except httpx.TimeoutException:
            raise format_request_timeout_error()

    def shutdown_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Shutting down a kernel with id {kernel_id}")

        kernel_id = kernel_id or DEFAULT_KERNEL_ID

        try:
            response = self._client.delete(
                url=f"{self._url}/contexts/{kernel_id}",
                timeout=request_timeout or self._connection_config.request_timeout,
            )
            err = extract_exception(response)
            if err:
                raise err
        except httpx.TimeoutException:
            raise format_request_timeout_error()

    def restart_kernel(
        self,
        kernel_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        logger.debug(f"Creating new kernel for language: {kernel_id}")

        kernel_id = kernel_id or DEFAULT_KERNEL_ID
        try:
            response = self._client.post(
                f"{self._url}/contexts/{kernel_id}/restart",
                timeout=request_timeout or self._connection_config.request_timeout,
            )

            err = extract_exception(response)
            if err:
                raise err
        except httpx.TimeoutException:
            raise format_request_timeout_error()

    def list_kernels(
        self,
        request_timeout: Optional[float] = None,
    ) -> List[Kernel]:
        try:
            response = self._client.get(
                f"{self._url}/contexts",
                timeout=request_timeout or self._connection_config.request_timeout,
            )

            err = extract_exception(response)
            if err:
                raise err

            return [Kernel(kernel_id=k["id"], name=k["name"]) for k in response.json()]
        except httpx.TimeoutException:
            raise format_request_timeout_error()


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
