from __future__ import annotations

import logging

from typing import Optional, Dict
from e2b import Sandbox

from e2b_code_interpreter.client import DefaultApi, ExecutionRequest
from e2b_code_interpreter.constants import TIMEOUT
from e2b_code_interpreter.models import Execution

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

    def exec_cell(
        self,
        code: str,
        kernel_id: Optional[str] = None,
        timeout: float = TIMEOUT,
    ) -> Execution:
        """
        Execute code in a notebook cell.

        :param code: Code to execute
        :param kernel_id: The ID of the kernel to execute the code on. If not provided, the default kernel is used.
        :param timeout: Timeout for the call

        :return: Result of the execution
        """
        logger.debug(f"Executing code in kernel {kernel_id}")

        with DefaultApi() as api_client:
            result = api_client.exec_post(ExecutionRequest(code=code), _request_timeout=timeout)

        logger.debug(
            f"Received result from kernel {kernel_id}, result: {result}"
        )

        return result
