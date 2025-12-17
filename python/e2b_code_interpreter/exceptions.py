import json
from dataclasses import dataclass

from e2b import TimeoutException


@dataclass
class ExecutionError:
    """
    Represents an error that occurred during the execution of a cell.
    The error contains the name of the error, the value of the error, and the traceback.
    """

    name: str
    """
    Name of the error.
    """
    value: str
    """
    Value of the error.
    """
    traceback: str
    """
    The raw traceback of the error.
    """

    def __init__(self, name: str, value: str, traceback: str, **kwargs):
        self.name = name
        self.value = value
        self.traceback = traceback

    def to_json(self) -> str:
        """
        Returns the JSON representation of the Error object.
        """
        data = {"name": self.name, "value": self.value, "traceback": self.traceback}
        return json.dumps(data)


def format_request_timeout_error() -> Exception:
    return TimeoutException(
        "Request timed out — the 'request_timeout' option can be used to increase this timeout",
    )


def format_execution_timeout_error() -> Exception:
    return TimeoutException(
        "Execution timed out — the 'timeout' option can be used to increase this timeout",
    )
