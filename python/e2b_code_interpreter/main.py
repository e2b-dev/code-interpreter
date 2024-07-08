from __future__ import annotations

import logging

from typing import Optional, Dict
from e2b import Sandbox


from e2b_code_interpreter.constants import TIMEOUT
from e2b_code_interpreter.models import Execution, Result, Logs, Error


from e2b_code_interpreter.client.client import Client
from e2b_code_interpreter.client.models import ExecutionRequest

from e2b_code_interpreter.client.api.default.post_execute import (
    sync_detailed as post_execute,
)

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

        client = Client(base_url=f"https://{self.get_host(8000)}")
        with client as client:
            execution = post_execute(client=client, body=ExecutionRequest(code=code))

        execution = execution.parsed
        if not execution:
            raise Exception("Failed to execute code")

        logger.debug(f"Received result: {execution} (Sandbox: {self.sandbox_id})")

        return Execution(
            results=(
                [Result(**result.to_dict()) for result in execution.results]
                if execution.results
                else None
            ),
            logs=(
                Logs(
                    stdout=execution.logs.stdout or None,
                    stderr=execution.logs.stderr or None,
                )
                if execution.logs
                else Logs()
            ),
            error=(Error(**execution.error.to_dict()) if execution.error else None),
        )
