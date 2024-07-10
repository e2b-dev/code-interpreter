from __future__ import annotations

from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class OutputType(Enum):
    """
    Represents the type of the data to send to the client.
    """

    STDOUT = "stdout"
    STDERR = "stderr"
    RESULT = "result"
    ERROR = "error"
    NUMBER_OF_EXECUTIONS = "number_of_executions"
    END_OF_EXECUTION = "end_of_execution"


class EndOfExecution(BaseModel):
    type: OutputType = OutputType.END_OF_EXECUTION


class NumberOfExecutions(BaseModel):
    type: OutputType = OutputType.NUMBER_OF_EXECUTIONS
    execution_count: int
