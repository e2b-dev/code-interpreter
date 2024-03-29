from typing import List, Optional
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
    traceback_raw: List[str]

    @property
    def traceback(self) -> str:
        """
        Returns the traceback as a single string.

        :return: The traceback as a single string.
        """
        return "\n".join(self.traceback_raw)


class DisplayData(dict):
    """
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.

    Dictionary that maps MIME types to their corresponding string representations of the data.
    MIME types are used to specify the nature and format of the data, allowing for the representation
    of various types of content such as text, images, and more. Each key in the interface is a MIME type
    string, and its value is the data associated with that MIME type, formatted as a string.
    """

    def __init__(self, *args, **kwargs: str):
        super().__init__(*args, **kwargs)

    def __str__(self):
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self["text/plain"]

    def _repr_html_(self):
        """
        Returns the HTML representation of the data.

        :return: The HTML representation of the data.
        """
        return self.get("text/html", None)

    def _repr_markdown_(self):
        """
        Returns the Markdown representation of the data.

        :return: The Markdown representation of the data.
        """
        return self.get("text/markdown", None)

    def _repr_svg_(self):
        """
        Returns the SVG representation of the data.

        :return: The SVG representation of the data.
        """
        return self.get("image/svg+xml", None)

    def _repr_png_(self):
        """
        Returns the PNG representation of the data.

        :return: The PNG representation of the data.
        """
        return self.get("image/png", None)

    def _repr_jpeg_(self):
        """
        Returns the JPEG representation of the data.

        :return: The JPEG representation of the data.
        """
        return self.get("image/jpeg", None)

    def _repr_pdf_(self):
        """
        Returns the PDF representation of the data.

        :return: The PDF representation of the data.
        """
        return self.get("application/pdf", None)

    def _repr_latex_(self):
        """
        Returns the LaTeX representation of the data.

        :return: The LaTeX representation of the data.
        """
        return self.get("text/latex", None)

    def _repr_json_(self):
        """
        Returns the JSON representation of the data.

        :return: The JSON representation of the data.
        """
        return self.get("application/json", None)

    def _repr_javascript_(self):
        """
        Returns the JavaScript representation of the data.

        :return: The JavaScript representation of the data.
        """
        return self.get("application/javascript", None)


class Cell(BaseModel):
    """
    Represents the result of an cell execution.

    result: Result of the last line executed interactively. It's a dictionary containing MIME type as key and data as value. The string representation of the result is stored under the key 'text/plain'.
    display_data: List of display calls, e.g. matplotlib plots. Each element is a dictionary containing MIME type as key and data as value.
    stdout: list of strings printed to stdout by prints, subprocesses, etc.
    stderr: list of strings printed to stderr by prints, subprocesses, etc.
    error: an Error object if an error occurred, None otherwise.
    """

    class Config:
        arbitrary_types_allowed = True

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
        return self.result["text/plain"]


class KernelException(Exception):
    """
    Exception raised when a kernel operation fails.
    """

    pass
