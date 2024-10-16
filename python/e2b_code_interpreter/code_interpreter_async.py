import logging
import httpx

from typing import Optional, Dict, overload, Union, Literal
from httpx import AsyncClient

from e2b import (
    AsyncSandbox as BaseAsyncSandbox,
    ConnectionConfig,
    InvalidArgumentException,
)

from e2b_code_interpreter.constants import (
    DEFAULT_TEMPLATE,
    JUPYTER_PORT,
    DEFAULT_TIMEOUT,
)
from e2b_code_interpreter.models import (
    Execution,
    ExecutionError,
    Context,
    Result,
    aextract_exception,
    parse_output,
    OutputHandler,
    OutputMessage,
)
from e2b_code_interpreter.exceptions import (
    format_execution_timeout_error,
    format_request_timeout_error,
)

logger = logging.getLogger(__name__)


class AsyncSandbox(BaseAsyncSandbox):
    """
    E2B cloud sandbox is a secure and isolated cloud environment.

    The sandbox allows you to:
    - Access Linux OS
    - Create, list, and delete files and directories
    - Run commands
    - Run isolated code
    - Access the internet

    Check docs [here](https://e2b.dev/docs).

    Use the `AsyncSandbox.create()` to create a new sandbox.

    Example:
    ```python
    from e2b_code_interpreter import AsyncSandbox
    sandbox = await AsyncSandbox.create()
    ```
    """

    default_template = DEFAULT_TEMPLATE

    def __init__(self, sandbox_id: str, connection_config: ConnectionConfig):
        super().__init__(sandbox_id=sandbox_id, connection_config=connection_config)

    @property
    def _jupyter_url(self) -> str:
        return f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(JUPYTER_PORT)}"

    @property
    def _client(self) -> AsyncClient:
        return AsyncClient(transport=self._transport)

    @overload
    async def run_code(
        self,
        code: str,
        language: Union[Literal["python"], None] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        on_error: Optional[OutputHandler[ExecutionError]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        """
        Runs the code as Python.

        Specify the `language` or `context` option to run the code as a different language or in a different `Context`.

        You can reference previously defined variables, imports, and functions in the code.

        :param code: Code to execute
        :param language: Language to use for code execution. If not defined, the default Python context is used.
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :param on_result: Callback for the `Result` object
        :param on_error: Callback for the `ExecutionError` object
        :param envs: Custom environment variables
        :param timeout: Timeout for the code execution in **seconds**
        :param request_timeout: Timeout for the request in **seconds**

        :return: `Execution` result object
        """
        ...

    @overload
    async def run_code(
        self,
        code: str,
        language: Optional[str] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        on_error: Optional[OutputHandler[ExecutionError]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        """
        Runs the code for the specified language.

        Specify the `language` or `context` option to run the code as a different language or in a different `Context`.
        If no language is specified, Python is used.

        You can reference previously defined variables, imports, and functions in the code.

        :param code: Code to execute
        :param language: Language to use for code execution. If not defined, the default Python context is used.
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :param on_result: Callback for the `Result` object
        :param on_error: Callback for the `ExecutionError` object
        :param envs: Custom environment variables
        :param timeout: Timeout for the code execution in **seconds**
        :param request_timeout: Timeout for the request in **seconds**

        :return: `Execution` result object
        """
        ...

    @overload
    async def run_code(
        self,
        code: str,
        context: Optional[Context] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        on_error: Optional[OutputHandler[ExecutionError]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        """
        Runs the code in the specified context, if not specified, the default context is used.

        Specify the `language` or `context` option to run the code as a different language or in a different `Context`.

        You can reference previously defined variables, imports, and functions in the code.

        :param code: Code to execute
        :param context: Concrete context to run the code in. If not specified, the default context for the language is used. It's mutually exclusive with the language.
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :param on_result: Callback for the `Result` object
        :param on_error: Callback for the `ExecutionError` object
        :param envs: Custom environment variables
        :param timeout: Timeout for the code execution in **seconds**
        :param request_timeout: Timeout for the request in **seconds**

        :return: `Execution` result object
        """
        ...

    async def run_code(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[Context] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        on_error: Optional[OutputHandler[ExecutionError]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        logger.debug(f"Executing code {code}")

        if context and language:
            raise InvalidArgumentException(
                "You can provide context or language, but not both at the same time."
            )

        timeout = None if timeout == 0 else (timeout or DEFAULT_TIMEOUT)
        request_timeout = request_timeout or self._connection_config.request_timeout
        context_id = context.id if context else None

        try:
            async with self._client.stream(
                "POST",
                f"{self._jupyter_url}/execute",
                json={
                    "code": code,
                    "context_id": context_id,
                    "language": language,
                    "env_vars": envs,
                },
                timeout=(request_timeout, timeout, request_timeout, request_timeout),
            ) as response:

                err = await aextract_exception(response)
                if err:
                    raise err

                execution = Execution()

                async for line in response.aiter_lines():
                    parse_output(
                        execution,
                        line,
                        on_stdout=on_stdout,
                        on_stderr=on_stderr,
                        on_result=on_result,
                        on_error=on_error,
                    )

                return execution
        except httpx.ReadTimeout:
            raise format_execution_timeout_error()
        except httpx.TimeoutException:
            raise format_request_timeout_error()

    async def create_code_context(
        self,
        cwd: Optional[str] = None,
        language: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> Context:
        """
        Creates a new context to run code in.

        :param cwd: Set the current working directory for the context, defaults to `/home/user`
        :param language: Language of the context. If not specified, defaults to Python
        :param request_timeout: Timeout for the request in **milliseconds**

        :return: Context object
        """
        logger.debug(f"Creating new {language} context")

        data = {}
        if language:
            data["language"] = language
        if cwd:
            data["cwd"] = cwd

        try:
            response = await self._client.post(
                f"{self._jupyter_url}/contexts",
                json=data,
                timeout=request_timeout or self._connection_config.request_timeout,
            )

            err = await aextract_exception(response)
            if err:
                raise err

            data = response.json()
            return Context.from_json(data)
        except httpx.TimeoutException:
            raise format_request_timeout_error()
