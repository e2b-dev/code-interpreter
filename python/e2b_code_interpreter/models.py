from typing import Dict, List, Optional
from pydantic import BaseModel


class Error(BaseModel):
    """
    Represents an error that occurred during execution.

    name: Name of the error.
    value: Value of the error.
    traceback: List of strings representing the traceback.
    """

    name: str
    value: str
    traceback: List[str]


MIMEType = str
DisplayData = Dict[MIMEType, str]
"""
Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.

Dictionary that maps MIME types to their corresponding string representations of the data.
MIME types are used to specify the nature and format of the data, allowing for the representation
of various types of content such as text, images, and more. Each key in the interface is a MIME type
string, and its value is the data associated with that MIME type, formatted as a string.
"""


class Cell(BaseModel):
    """
    Represents the result of an cell execution.

    result: Result of the last line executed interactively. It's a dictionary containing MIME type as key and data as value. The string representation of the result is stored under the key 'text/plain'.
    display_data: List of display calls, e.g. matplotlib plots. Each element is a dictionary containing MIME type as key and data as value.
    stdout: list of strings printed to stdout by prints, subprocesses, etc.
    stderr: list of strings printed to stderr by prints, subprocesses, etc.
    error: an Error object if an error occurred, None otherwise.
    """

    result: DisplayData = {}
    display_data: List[DisplayData] = []
    stdout: List[str] = []
    stderr: List[str] = []
    error: Optional[Error] = None

    @property
    def text(self) -> str:
        """
        Returns the text representation of the result.

        :return: The text representation of the result.
        """
        return self.result.get("text/plain", None)


class KernelException(Exception):
    """
    Exception raised when a kernel operation fails.
    """

    pass
