from __future__ import annotations

import logging

from typing import Optional, Dict
from e2b import Sandbox

from e2b_code_interpreter.client import (
    DefaultApi,
    ExecutionRequest,
    ApiClient,
    Configuration,
)
from e2b_code_interpreter.constants import TIMEOUT
from e2b_code_interpreter.models import Execution, Result, Logs, Error

logger = logging.getLogger(__name__)


class CodeInterpreter(Sandbox):
    """
    E2B code interpreter sandbox extension.
    """

    default_template = "ci-no-ws"

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

    def exec_code(
        self,
        code: str,
        language: Optional[str] = None,
        timeout: float = TIMEOUT,
    ) -> Execution:
        """
        Execute code in a notebook cell.

        :param code: Code to execute
        :param language: Language of the code to be executed
        :param timeout: Timeout for the call

        :return: Result of the execution
        """
        logger.debug(
            f"Executing code {code} for language {language} (Sandbox: {self.sandbox_id})"
        )

        configuration = Configuration(host=f"https://{self.get_host(8000)}")
        with ApiClient(configuration=configuration) as client:
            api_client = DefaultApi(api_client=client)
            execution = api_client.execute_post(
                ExecutionRequest(code=code, language=language), _request_timeout=timeout
            )

        logger.debug(f"Received result: {execution} (Sandbox: {self.sandbox_id})")

        return Execution(
            results=(
                [
                    Result(**result.model_dump(exclude={"additional_properties"}))
                    for result in execution.results
                ]
                if execution.results
                else None
            ),
            logs=(
                Logs(stdout=execution.logs.stdout, stderr=execution.logs.stderr)
                if execution.logs
                else Logs()
            ),
            error=(
                Error(**execution.error.model_dump(exclude={"additional_properties"}))
                if execution.error
                else None
            ),
        )
