from typing import List, Optional, Iterable, Dict
from pydantic import BaseModel


class Error(BaseModel):
    """
    Represents an error that occurred during execution.
    """

    name: str
    "Name of the exception."
    value: str
    "Value of the exception."
    traceback_raw: List[str]
    "List of strings representing the traceback."

    @property
    def traceback(self) -> str:
        """
        Returns the traceback as a single string.

        :return: The traceback as a single string.
        """
        return "\n".join(self.traceback_raw)


class MIMEType(str):
    """
    Represents a MIME type.
    """


class Data:
    """
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.

    Dictionary that maps MIME types to their corresponding string representations of the data.
    MIME types are used to specify the nature and format of the data, allowing for the representation
    of various types of content such as text, images, and more. Each key in the interface is a MIME type
    string, and its value is the data associated with that MIME type, formatted as a string.
    """
    is_main_result: bool
    "Whether this data is the main result of the cell."

    raw: Dict[MIMEType, str]
    "Dictionary that maps MIME types to their corresponding string representations of the data."

    text: str
    "Text representation of the data. Always present."
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

    def __init__(self, is_main_result: bool, data: [MIMEType, str]):
        self.is_main_result = is_main_result
        self.raw = data

        self.text = data["text/plain"]
        self.html = data.get("text/html", None)
        self.markdown = data.get("text/markdown", None)
        self.svg = data.get("image/svg+xml", None)
        self.png = data.get("image/png", None)
        self.jpeg = data.get("image/jpeg", None)
        self.pdf = data.get("application/pdf", None)
        self.latex = data.get("text/latex", None)
        self.json = data.get("application/json", None)
        self.javascript = data.get("application/javascript", None)

    def keys(self) -> Iterable[str]:
        """
        Returns the MIME types of the data.

        :return: The MIME types of the data.
        """
        return self.raw.keys()

    def __str__(self) -> str:
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self.text

    def _repr_html_(self) -> str:
        """
        Returns the HTML representation of the data.

        :return: The HTML representation of the data.
        """
        return self.html

    def _repr_markdown_(self) -> str:
        """
        Returns the Markdown representation of the data.

        :return: The Markdown representation of the data.
        """
        return self.markdown

    def _repr_svg_(self) -> str:
        """
        Returns the SVG representation of the data.

        :return: The SVG representation of the data.
        """
        return self.svg

    def _repr_png_(self) -> str:
        """
        Returns the base64 representation of the PNG data.

        :return: The base64 representation of the PNG data.
        """
        return self.png

    def _repr_jpeg_(self) -> str:
        """
        Returns the base64 representation of the JPEG data.

        :return: The base64 representation of the JPEG data.
        """
        return self.jpeg

    def _repr_pdf_(self) -> str:
        """
        Returns the PDF representation of the data.

        :return: The PDF representation of the data.
        """
        return self.pdf

    def _repr_latex_(self) -> str:
        """
        Returns the LaTeX representation of the data.

        :return: The LaTeX representation of the data.
        """
        return self.latex

    def _repr_json_(self) -> dict:
        """
        Returns the JSON representation of the data.

        :return: The JSON representation of the data.
        """
        return self.json

    def _repr_javascript_(self) -> str:
        """
        Returns the JavaScript representation of the data.

        :return: The JavaScript representation of the data.
        """
        return self.javascript


class Logs(BaseModel):
    """
    Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
    """

    stdout: List[str] = []
    "List of strings printed to stdout by prints, subprocesses, etc."
    stderr: List[str] = []
    "List of strings printed to stderr by prints, subprocesses, etc."


class Execution(BaseModel):
    """
    Represents the result of a cell execution.
    """

    class Config:
        arbitrary_types_allowed = True

    data: List[Data] = []
    "List of display calls, e.g. matplotlib plots."
    logs: Logs = Logs()
    "Logs printed to stdout and stderr during execution."
    error: Optional[Error] = None
    "Error object if an error occurred, None otherwise."

    @property
    def text(self) -> Optional[str]:
        """
        Returns the text representation of the result.

        :return: The text representation of the result.
        """
        for d in self.data:
            if d.is_main_result:
                return d.raw["text/plain"]


class KernelException(Exception):
    """
    Exception raised when a kernel operation fails.
    """

    pass
