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
    END_OF_EXECUTION = "end_of_execution"


class Output(BaseModel):
    type: OutputType

    text: Optional[str] = None
    html: Optional[str] = None
    markdown: Optional[str] = None
    svg: Optional[str] = None
    png: Optional[str] = None
    jpeg: Optional[str] = None
    pdf: Optional[str] = None
    latex: Optional[str] = None
    json: Optional[dict] = None
    javascript: Optional[str] = None
    extra: Optional[dict] = None
    is_main_result: Optional[bool] = None

    stdout: Optional[str] = None
    stderr: Optional[str] = None

    name: Optional[str] = None
    value: Optional[str] = None
    traceback: Optional[str] = None

    def __init__(self, type: OutputType,  data: Dict[str, str] = None, is_main_result:Optional[bool] = None):
        super().__init__()
        self.type = type

        self.is_main_result = is_main_result

        self.text = data.pop("text/plain", None)
        self.html = data.pop("text/html", None)
        self.markdown = data.pop("text/markdown", None)
        self.svg = data.pop("image/svg+xml", None)
        self.png = data.pop("image/png", None)
        self.jpeg = data.pop("image/jpeg", None)
        self.pdf = data.pop("application/pdf", None)
        self.latex = data.pop("text/latex", None)
        self.json = data.pop("application/json", None)
        self.javascript = data.pop("application/javascript", None)

        self.name = data.pop("ename", None)
        self.value = data.pop("evalue", None) or data.pop("text", None)
        self.traceback = data.pop("traceback", None)
        if self.traceback:
            self.traceback = "\n".join(self.traceback)

        self.extra = data

    def __str__(self) -> Optional[str]:
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self.text

    def __repr__(self) -> str:
        if self.type == OutputType.RESULT:
            return f"Result({self.text})"
        elif self.type == OutputType.ERROR:
            return f"Error({self.name}, {self.value}, {self.traceback})"
        elif self.type == OutputType.STDOUT:
            return f"Stdout({self.stdout})"
        elif self.type == OutputType.STDERR:
            return f"Stderr({self.stderr})"
