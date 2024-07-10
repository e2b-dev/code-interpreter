from __future__ import annotations


from typing import Optional
from pydantic import BaseModel

from api.models.output import OutputType

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Result(BaseModel):
    """
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
    The result is similar to the structure returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics

    The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
    as a string, and the result can contain multiple types of data. The display calls don't have to have text representation,
    for the actual result the representation is always present for the result, the other representations are always optional.

    The class also provides methods to display the data in a Jupyter notebook.
    """
    type: OutputType = OutputType.RESULT

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
    "Extra data that can be included. Not part of the standard types."

    is_main_result: Optional[bool] = None
    "Whether this data is the result of the cell. Data can be produced by display calls of which can be multiple in a cell."

    def __init__(self, is_main_result: bool, data: [str, str]):
        super().__init__()
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
        self.extra = data

    def __str__(self) -> Optional[str]:
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self.text

    def __repr__(self) -> str:
        return f"Result({self.text})"
