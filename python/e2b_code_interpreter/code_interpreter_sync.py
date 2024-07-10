import json
import logging

from typing import Optional, Dict, Callable, TypeVar
from httpx import HTTPTransport, Client
from e2b import Sandbox, Stderr, Stdout, ConnectionConfig

from e2b_code_interpreter.constants import DEFAULT_TEMPLATE, JUPYTER_PORT
from e2b_code_interpreter.models import Execution, Result, Error


logger = logging.getLogger(__name__)

T = TypeVar("T")

OutputHandler = Callable[[T], None]


class JupyterExtension:
    _exec_timeout = 300

    def __init__(
        self,
        url: str,
        transport: HTTPTransport,
        connection_config: ConnectionConfig,
    ):
        self._url = url
        self._transport = transport
        self._connection_config = connection_config

    def exec_code(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        language: Optional[str] = None,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ):
        logger.debug(f"Executing code {code} for language {language}")

        timeout = None if timeout == 0 else (timeout or self._exec_timeout)
        request_timeout = request_timeout or self._connection_config.request_timeout

        with Client(transport=self._transport) as client:
            response = client.post(
                self._url,
                json={
                    "code": code,
                    # "language": language,
                    # "kernel_id": kernel_id,
                },
                timeout=(request_timeout, timeout, request_timeout, request_timeout),
            )

            response.raise_for_status()

            execution = Execution()

            for line in response.iter_lines():
                data = json.loads(line)
                data_type = data.pop("type")

                if data_type == "result":
                    result = Result(**data)
                    execution.results.append(result)
                    if on_result:
                        on_result(result)
                elif data_type == "stdout":
                    execution.logs.stdout += data["value"]
                    if on_stdout:
                        on_stdout(data["value"])
                elif data_type == "stderr":
                    execution.logs.stderr += data["value"]
                    if on_stderr:
                        on_stderr(data["value"])
                elif data_type == "error":
                    execution.error = Error(**data)

            return execution


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

        jupyter_url = f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(self._jupyter_port)}/execute"
        self._notebook = JupyterExtension(
            jupyter_url, self._transport, self.connection_config
        )
