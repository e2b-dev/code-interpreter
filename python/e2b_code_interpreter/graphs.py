import enum
from typing import List, Tuple, Any, Optional, Union


class GraphType(str, enum.Enum):
    """
    Graph types
    """

    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    PIE = "pie"
    BOX_AND_WHISKER = "box_and_whisker"
    SUPERGRAPH = "supergraph"
    UNKNOWN = "unknown"


class ScaleType(str, enum.Enum):
    """
    Ax scale types
    """

    LINEAR = "linear"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    LOG = "log"
    SYMLOG = "symlog"
    LOGIT = "logit"
    FUNCTION = "function"
    FUNCTIONLOG = "functionlog"
    ASINH = "asinh"
    UNKNOWN = "unknown"


class Graph:
    """
    Extracted data from a graph. It's useful for building an interactive graphs or custom visualizations.
    """

    type: GraphType
    title: str

    elements: List[Any]

    def __init__(self, **kwargs):
        self.type = GraphType(kwargs["type"] or GraphType.UNKNOWN)
        self.title = kwargs["title"]
        self.elements = kwargs["elements"]


class Graph2D(Graph):
    x_label: Optional[str]
    y_label: Optional[str]
    x_unit: Optional[str]
    y_unit: Optional[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_label = kwargs["x_label"]
        self.y_label = kwargs["y_label"]
        self.x_unit = kwargs["x_unit"]
        self.y_unit = kwargs["y_unit"]


class PointData:
    label: str
    points: List[Tuple[Union[str, float], Union[str, float]]]

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.points = [(x, y) for x, y in kwargs["points"]]


class PointGraph(Graph2D):
    x_ticks: List[Union[str, float]]
    x_tick_labels: List[str]
    x_scale: ScaleType

    y_ticks: List[Union[str, float]]
    y_tick_labels: List[str]
    y_scale: ScaleType

    elements: List[PointData]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_label = kwargs["x_label"]

        try:
            self.x_scale = ScaleType(kwargs.get("x_scale"))
        except ValueError:
            self.x_scale = ScaleType.UNKNOWN

        self.x_ticks = kwargs["x_ticks"]
        self.x_tick_labels = kwargs["x_tick_labels"]

        self.y_label = kwargs["y_label"]

        try:
            self.y_scale = ScaleType(kwargs.get("y_scale"))
        except ValueError:
            self.y_scale = ScaleType.UNKNOWN

        self.y_ticks = kwargs["y_ticks"]
        self.y_tick_labels = kwargs["y_tick_labels"]

        self.elements = [PointData(**d) for d in kwargs["elements"]]


class LineGraph(PointGraph):
    type = GraphType.LINE


class ScatterGraph(PointGraph):
    type = GraphType.SCATTER


class BarData:
    label: str
    group: str
    value: str

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.value = kwargs["value"]
        self.group = kwargs["group"]


class BarGraph(Graph2D):
    type = GraphType.BAR

    elements: List[BarData]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = [BarData(**d) for d in kwargs["elements"]]


class PieData:
    label: str
    angle: float
    radius: float

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.angle = kwargs["angle"]
        self.radius = kwargs["radius"]


class PieGraph(Graph):
    type = GraphType.PIE

    elements: List[PieData]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = [PieData(**d) for d in kwargs["elements"]]


class BoxAndWhiskerData:
    label: str
    min: float
    first_quartile: float
    median: float
    third_quartile: float
    max: float

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.min = kwargs["min"]
        self.first_quartile = kwargs["first_quartile"]
        self.median = kwargs["median"]
        self.third_quartile = kwargs["third_quartile"]
        self.max = kwargs["max"]


class BoxAndWhiskerGraph(Graph2D):
    type = GraphType.BOX_AND_WHISKER

    elements: List[BoxAndWhiskerData]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = [BoxAndWhiskerData(**d) for d in kwargs["elements"]]


class SuperGraph(Graph):
    type = GraphType.SUPERGRAPH

    elements: List[
        Union[LineGraph, ScatterGraph, BarGraph, PieGraph, BoxAndWhiskerGraph]
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = [deserialize_graph(g) for g in kwargs["elements"]]


GraphTypes = Union[
    LineGraph, ScatterGraph, BarGraph, PieGraph, BoxAndWhiskerGraph, SuperGraph
]


def deserialize_graph(data: Optional[dict]) -> Optional[GraphTypes]:
    if not data:
        return None

    if data["type"] == GraphType.LINE:
        graph = LineGraph(**data)
    elif data["type"] == GraphType.SCATTER:
        graph = ScatterGraph(**data)
    elif data["type"] == GraphType.BAR:
        graph = BarGraph(**data)
    elif data["type"] == GraphType.PIE:
        graph = PieGraph(**data)
    elif data["type"] == GraphType.BOX_AND_WHISKER:
        graph = BoxAndWhiskerGraph(**data)
    elif data["type"] == GraphType.SUPERGRAPH:
        graph = SuperGraph(**data)
    else:
        graph = Graph(**data)

    return graph
