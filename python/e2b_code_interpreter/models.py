import json
from typing import List, Optional, Iterable, Dict


class Error:
    """
    Represents an error that occurred during the execution of a cell.
    The error contains the name of the error, the value of the error, and the traceback.
    """

    name: str
    "Name of the exception."
    value: str
    "Value of the exception."
    traceback_raw: List[str]
    "List of strings representing the traceback."

    def __init__(self, name: str, value: str, traceback: List[str]):
        self.name = name
        self.value = value
        self.traceback_raw = traceback

    @property
    def traceback(self) -> str:
        """
        Returns the traceback as a single string.

        :return: The traceback as a single string.
        """
        return "\n".join(self.traceback_raw)

    def to_json(self) -> str:
        """
        Returns the JSON representation of the Error object.
        """
        data = {"name": self.name, "value": self.value, "traceback": self.traceback}
        return json.dumps(data)


class MIMEType(str):
    """
    Represents a MIME type.
    """


class Result:
    """
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
    The result is similar to the structure returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics

    The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
    as a string, and the result can contain multiple types of data. The display calls don't have to have text representation,
    for the actual result the representation is always present for the result, the other representations are always optional.

    The class also provides methods to display the data in a Jupyter notebook.
    """

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

    is_main_result: bool
    "Whether this data is the result of the cell. Data can be produced by display calls of which can be multiple in a cell."

    def __getitem__(self, item):
        return getattr(self, item)

    # Allows to iterate over formats()
    def __init__(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        markdown: Optional[str] = None,
        svg: Optional[str] = None,
        png: Optional[str] = None,
        jpeg: Optional[str] = None,
        pdf: Optional[str] = None,
        latex: Optional[str] = None,
        json: Optional[dict] = None,
        javascript: Optional[str] = None,
        is_main_result: bool = False,
        extra: Optional[dict] = None,
    ):
        self.text = text
        self.html = html
        self.markdown = markdown
        self.svg = svg
        self.png = png
        self.jpeg = jpeg
        self.pdf = pdf
        self.latex = latex
        self.json = json
        self.javascript = javascript
        self.is_main_result = is_main_result
        self.extra = extra or {}

    def formats(self) -> Iterable[str]:
        """
        Returns all available formats of the result.

        :return: All available formats of the result in MIME types.
        """
        formats = []
        if self.html:
            formats.append("html")
        if self.markdown:
            formats.append("markdown")
        if self.svg:
            formats.append("svg")
        if self.png:
            formats.append("png")
        if self.jpeg:
            formats.append("jpeg")
        if self.pdf:
            formats.append("pdf")
        if self.latex:
            formats.append("latex")
        if self.json:
            formats.append("json")
        if self.javascript:
            formats.append("javascript")

        for key in self.extra:
            formats.append(key)

        return formats

    def __str__(self) -> Optional[str]:
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self.text

    def __repr__(self) -> str:
        return f"Result({self.text})"

    def _repr_html_(self) -> Optional[str]:
        """
        Returns the HTML representation of the data.

        :return: The HTML representation of the data.
        """
        return self.html

    def _repr_markdown_(self) -> Optional[str]:
        """
        Returns the Markdown representation of the data.

        :return: The Markdown representation of the data.
        """
        return self.markdown

    def _repr_svg_(self) -> Optional[str]:
        """
        Returns the SVG representation of the data.

        :return: The SVG representation of the data.
        """
        return self.svg

    def _repr_png_(self) -> Optional[str]:
        """
        Returns the base64 representation of the PNG data.

        :return: The base64 representation of the PNG data.
        """
        return self.png

    def _repr_jpeg_(self) -> Optional[str]:
        """
        Returns the base64 representation of the JPEG data.

        :return: The base64 representation of the JPEG data.
        """
        return self.jpeg

    def _repr_pdf_(self) -> Optional[str]:
        """
        Returns the PDF representation of the data.

        :return: The PDF representation of the data.
        """
        return self.pdf

    def _repr_latex_(self) -> Optional[str]:
        """
        Returns the LaTeX representation of the data.

        :return: The LaTeX representation of the data.
        """
        return self.latex

    def _repr_json_(self) -> Optional[dict]:
        """
        Returns the JSON representation of the data.

        :return: The JSON representation of the data.
        """
        return self.json

    def _repr_javascript_(self) -> Optional[str]:
        """
        Returns the JavaScript representation of the data.

        :return: The JavaScript representation of the data.
        """
        return self.javascript


class Logs:
    """
    Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
    """

    stdout: Optional[str] = None
    "List of strings printed to stdout by prints, subprocesses, etc."
    stderr: Optional[str] = None
    "List of strings printed to stderr by prints, subprocesses, etc."

    def __init__(
        self, stdout: Optional[List[str]] = None, stderr: Optional[List[str]] = None
    ):
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        return f"Logs(stdout: {self.stdout}, stderr: {self.stderr})"

    def to_json(self) -> str:
        """
        Returns the JSON representation of the Logs object.
        """
        data = {"stdout": self.stdout, "stderr": self.stderr}
        return json.dumps(data)


def serialize_results(results: List[Result]) -> List[Dict[str, str]]:
    """
    Serializes the results to JSON.
    """
    serialized = []
    for result in results:
        serialized_dict = {key: result[key] for key in result.formats()}
        serialized_dict["text"] = result.text
        serialized.append(serialized_dict)
    return serialized


class Execution:
    """
    Represents the result of a cell execution.
    """

    results: List[Result] = []
    "List of the result of the cell (interactively interpreted last line), display calls (e.g. matplotlib plots)."
    logs: Logs = Logs()
    "Logs printed to stdout and stderr during execution."
    error: Optional[Error] = None
    "Error object if an error occurred, None otherwise."
    execution_count: Optional[int] = None
    "Execution count of the cell."

    def __init__(self, **kwargs):
        self.results = kwargs.pop("results", [])
        self.logs = kwargs.pop("logs", Logs())
        self.error = kwargs.pop("error", None)
        self.execution_count = kwargs.pop("execution_count", None)

    def __repr__(self):
        return f"Execution(Results: {self.results}, Logs: {self.logs}, Error: {self.error})"

    @property
    def text(self) -> Optional[str]:
        """
        Returns the text representation of the result.

        :return: The text representation of the result.
        """
        for d in self.results:
            if d.is_main_result:
                return d.text

    def to_json(self) -> str:
        """
        Returns the JSON representation of the Execution object.
        """
        data = {
            "results": serialize_results(self.results),
            "logs": self.logs.to_json(),
            "error": self.error.to_json() if self.error else None,
        }
        return json.dumps(data)


class KernelException(Exception):
    """
    Exception raised when a kernel operation fails.
    """

    pass
