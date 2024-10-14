import logging
import httpx

from typing import Optional, Dict
from httpx import Client
from e2b import Sandbox as BaseSandbox

from e2b_code_interpreter.constants import (
    DEFAULT_TEMPLATE,
    JUPYTER_PORT,
    DEFAULT_TIMEOUT,
)
from e2b_code_interpreter.models import (
    Execution,
    Context,
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


class Sandbox(BaseSandbox):
    default_template = DEFAULT_TEMPLATE

    @property
    def _jupyter_url(self) -> str:
        return f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(JUPYTER_PORT)}"

    @property
    def _client(self) -> Client:
        return Client(transport=self._transport)

    def run_code(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[Context] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        """
        Runs the code in the specified context, if not specified, the default context is used.
        You can reference previously defined variables, imports, and functions in the code.

        :param code: The code to execute
        :param language: Language of the code. If not specified and context_id is not provided, the default Python context is used.
        :param context: The context to run the code in. If not specified, the default context for the language is used. It's mutually exclusive with language.
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :param on_result: Callback for the `Result` object
        :param envs: Environment variables
        :param timeout: Max time to wait for the execution to finish
        :param request_timeout: Max time to wait for the request to finish
        :return: Execution object
        """
        logger.debug(f"Executing code {code}")

        if language and context:
            raise ValueError("Only one of context_id or language can be provided")

        timeout = None if timeout == 0 else (timeout or DEFAULT_TIMEOUT)
        request_timeout = request_timeout or self._connection_config.request_timeout
        context_id = context.id if context else None

        try:
            with self._client.stream(
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

    def create_code_context(
        self,
        cwd: Optional[str] = None,
        language: Optional[str] = None,
        envs: Optional[Dict[str, str]] = None,
        request_timeout: Optional[float] = None,
    ) -> Context:
        """
        Creates a new context to run code in.

        :param cwd: Set the current working directory for the context
        :param language: Language of the context. If not specified, the default Python context is used.
        :param envs: Environment variables
        :param request_timeout: Max time to wait for the request to finish
        :return: Context id
        """
        logger.debug(f"Creating new {language} context")

        data = {}
        if language:
            data["language"] = language
        if cwd:
            data["cwd"] = cwd
        if envs:
            data["env_vars"] = envs

        try:
            response = self._client.post(
                f"{self._jupyter_url}/contexts",
                json=data,
                timeout=request_timeout or self._connection_config.request_timeout,
            )

            err = extract_exception(response)
            if err:
                raise err

            data = response.json()
            return Context.from_json(data)
        except httpx.TimeoutException:
            raise format_request_timeout_error()
