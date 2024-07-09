from __future__ import annotations

import json
import logging

from typing import Optional, Dict

import requests
from e2b import Sandbox


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

        execution = Execution()
        # with requests.get(f"https://{self.get_host(8000)}/execution", stream=True) as r:
        with requests.get(f"http://localhost:8000/execution", stream=True) as r:
            print(r)
            for line in r.iter_lines():
                data = json.loads(line.decode("utf-8"))
                data_type = data.pop("type")

                if data_type == "result":
                    result = Result(**data)
                    execution.results.append(result)
                elif data_type == "stdout":
                    execution.logs.stdout += data["value"]
                elif data_type == "stderr":
                    execution.logs.stderr += data["value"]
                elif data_type == "error":
                    execution.error = Error(**data)

        print("Done")
        return execution

        # if not execution:
        #     raise Exception("Failed to execute code")
        #
        # logger.debug(f"Received result: {execution} (Sandbox: {self.sandbox_id})")
        #
        # return Execution(
        #     results=(
        #         [Result(**result.to_dict()) for result in execution.results]
        #         if execution.results
        #         else None
        #     ),
        #     logs=(
        #         Logs(
        #             stdout=execution.logs.stdout or None,
        #             stderr=execution.logs.stderr or None,
        #         )
        #         if execution.logs
        #         else Logs()
        #     ),
        #     error=(Error(**execution.error.to_dict()) if execution.error else None),
        # )
