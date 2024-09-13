import json

from e2b import NotFoundException, TimeoutException, SandboxException
from dataclasses import dataclass, field
from typing import (
    List,
    Optional,
    Iterable,
    Dict,
    TypeVar,
    Callable,
    Awaitable,
    Any,
    Union,
)

from httpx import Response

from .graphs import Graph, deserialize_graph

T = TypeVar("T")
OutputHandler = Union[
    Callable[[T], Any],
    Callable[[T], Awaitable[Any]],
]


@dataclass
class OutputMessage:
    line: str
    timestamp: int
    """
    Unix epoch in nanoseconds
    """
    error: bool = False

    def __str__(self):
        return self.line


@dataclass
class ExecutionError:
    """
    Represents an error that occurred during the execution of a cell.
    The error contains the name of the error, the value of the error, and the traceback.
    """

    name: str
    value: str
    traceback: str

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


class MIMEType(str):
    """
    Represents a MIME type.
    """


@dataclass
class Result:
    """
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
    The result is similar to the structure returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics

    The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
    as a string, and the result can contain multiple types of data. The display calls don't have to have text representation,
    for the actual result the representation is always present for the result, the other representations are always optional.

    The class also provides methods to display the data in a Jupyter notebook.
    """

    def __getitem__(self, item):
        return getattr(self, item)

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
    data: Optional[dict] = None
    graph: Optional[Graph] = None
    is_main_result: bool = False
    """Whether this data is the result of the cell. Data can be produced by display calls of which can be multiple in a cell."""
    extra: Optional[dict] = None
    """Extra data that can be included. Not part of the standard types."""

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
        data: Optional[dict] = None,
        graph: Optional[dict] = None,
        is_main_result: bool = False,
        extra: Optional[dict] = None,
        **kwargs,  # Allows for future expansion
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
        self.data = data
        self.graph = deserialize_graph(graph) if graph else None
        self.is_main_result = is_main_result
        self.extra = extra

    def formats(self) -> Iterable[str]:
        """
        Returns all available formats of the result.

        :return: All available formats of the result in MIME types.
        """
        formats = []
        if self.text:
            formats.append("text")
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
        if self.data:
            formats.append("data")
        if self.graph:
            formats.append("graph")

        if self.extra:
            for key in self.extra:
                formats.append(key)

        return formats

    def __str__(self) -> Optional[str]:
        """
        Returns the text representation of the data.

        :return: The text representation of the data.
        """
        return self.__repr__()

    def __repr__(self) -> str:
        if self.text:
            return f"Result({self.text})"
        else:
            return "Result(Formats: " + ", ".join(self.formats()) + ")"

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


@dataclass(repr=False)
class Logs:
    """
    Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
    """

    stdout: List[str] = field(default_factory=list)
    """List of strings printed to stdout by prints, subprocesses, etc."""
    stderr: List[str] = field(default_factory=list)
    """List of strings printed to stderr by prints, subprocesses, etc."""

    def __init__(self, stdout: List[str] = None, stderr: List[str] = None, **kwargs):
        self.stdout = stdout or []
        self.stderr = stderr or []

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


@dataclass(repr=False)
class Execution:
    """
    Represents the result of a cell execution.
    """

    results: List[Result] = field(default_factory=list)
    """List of the result of the cell (interactively interpreted last line), display calls (e.g. matplotlib plots)."""
    logs: Logs = field(default_factory=Logs)
    """Logs printed to stdout and stderr during execution."""
    error: Optional[ExecutionError] = None
    """Error object if an error occurred, None otherwise."""
    execution_count: Optional[int] = None
    """Execution count of the cell."""

    def __init__(
        self,
        results: List[Result] = None,
        logs: Logs = None,
        error: Optional[ExecutionError] = None,
        execution_count: Optional[int] = None,
        **kwargs,
    ):
        self.results = results or []
        self.logs = logs or Logs()
        self.error = error
        self.execution_count = execution_count

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


async def aextract_exception(res: Response):
    if res.is_success:
        return None

    await res.aread()
    return extract_exception(res)


def extract_exception(res: Response):
    if res.is_success:
        return None

    res.read()
    return format_exception(res)


def format_exception(res: Response):
    if res.is_success:
        return None

    if res.status_code == 404:
        return NotFoundException(res.text)
    elif res.status_code == 502:
        return TimeoutException(
            f"{res.text}: This error is likely due to sandbox timeout. You can modify the sandbox timeout by passing 'timeout' when starting the sandbox or calling '.set_timeout' on the sandbox with the desired timeout."
        )
    else:
        return SandboxException(f"{res.status_code}: {res.text}")


def parse_output(
    execution: Execution,
    output: str,
    on_stdout: Optional[OutputHandler[OutputMessage]] = None,
    on_stderr: Optional[OutputHandler[OutputMessage]] = None,
    on_result: Optional[OutputHandler[Result]] = None,
):
    data = json.loads(output)
    data_type = data.pop("type")

    if data_type == "result":
        result = Result(**data)
        execution.results.append(result)
        if on_result:
            on_result(result)
    elif data_type == "stdout":
        execution.logs.stdout.append(data["text"])
        if on_stdout:
            on_stdout(OutputMessage(data["text"], data["timestamp"], False))
    elif data_type == "stderr":
        execution.logs.stderr.append(data["text"])
        if on_stderr:
            on_stderr(OutputMessage(data["text"], data["timestamp"], True))
    elif data_type == "error":
        execution.error = ExecutionError(data["name"], data["value"], data["traceback"])
    elif data_type == "number_of_executions":
        execution.execution_count = data["execution_count"]


@dataclass
class Kernel:
    kernel_id: str
    name: str

    def __init__(self, kernel_id: str, name: str, **kwargs):
        self.kernel_id = kernel_id
        self.name = name
