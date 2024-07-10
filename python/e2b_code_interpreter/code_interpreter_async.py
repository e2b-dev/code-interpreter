import json
import logging
import inspect

from typing import Optional
from httpx import AsyncHTTPTransport, AsyncClient
from e2b import AsyncSandbox, ConnectionConfig, Stderr, Stdout, OutputHandler

from e2b_code_interpreter.constants import DEFAULT_TEMPLATE, JUPYTER_PORT
from e2b_code_interpreter.models import Execution, Result, Error


logger = logging.getLogger(__name__)


class JupyterExtension:
    _exec_timeout = 300

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

        execution = Execution()

        async with AsyncClient(transport=self._transport) as client:
            async with client.stream(
                "POST",
                self._url,
                json={
                    "code": code,
                    # "language": language,
                    # "kernel_id": kernel_id,
                },
                timeout=(request_timeout, timeout, request_timeout, request_timeout),
            ) as response:

                response.raise_for_status()

                async for line in response.aiter_lines():
                    data = json.loads(line)
                    data_type = data.pop("type")

                    if data_type == "result":
                        result = Result(**data)
                        execution.results.append(result)
                        if on_result:
                            cb = on_result(result)
                            if inspect.isawaitable(cb):
                                await cb
                    elif data_type == "stdout":
                        execution.logs.stdout += data["value"]
                        if on_stdout:
                            cb = on_stdout(data["value"])
                            if inspect.isawaitable(cb):
                                await cb
                    elif data_type == "stderr":
                        execution.logs.stderr += data["value"]
                        if on_stderr:
                            cb = on_stderr(data["value"])
                            if inspect.isawaitable(cb):
                                await cb
                    elif data_type == "error":
                        execution.error = Error(**data)

            return execution


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
