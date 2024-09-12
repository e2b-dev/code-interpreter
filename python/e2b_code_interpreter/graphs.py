import enum
from typing import List, Tuple, Any, Optional, Union


class GraphType(enum.Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    PIE = "pie"
    BOX_AND_WHISKER = "box_and_whisker"
    SUPERGRAPH = "supergraph"
    UNKNOWN = "unknown"


class Graph:
    type: GraphType
    title: str

    elements: List[Any]

    def __init__(self, **kwargs):
        self.type = GraphType(kwargs["type"])
        self.title = kwargs["title"]


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
    points: List[Tuple[float, float]]

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.points = [(float(x), float(y)) for x, y in kwargs["points"]]


class PointGraph(Graph2D):
    x_ticks: List[float]
    x_tick_labels: List[str]
    y_ticks: List[float]
    y_tick_labels: List[str]

    elements: List[PointData]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_label = kwargs["x_label"]
        self.y_label = kwargs["y_label"]
        self.x_unit = kwargs["x_unit"]
        self.y_unit = kwargs["y_unit"]
        self.x_ticks = kwargs["x_ticks"]
        self.x_tick_labels = kwargs["x_tick_labels"]
        self.y_ticks = kwargs["y_ticks"]
        self.y_tick_labels = kwargs["y_tick_labels"]
        self.elements = [PointData(**d) for d in kwargs["elements"]]


class LineGraph(PointGraph):
    type = GraphType.LINE


class ScatterGraph(PointGraph):
    type = GraphType.SCATTER


class BarData:
    label: str
    value: str

    def __init__(self, **kwargs):
        self.label = kwargs["label"]
        self.value = kwargs["value"]


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

    if data["type"] == GraphType.LINE.value:
        graph = LineGraph(**data)
    elif data["type"] == GraphType.SCATTER.value:
        graph = ScatterGraph(**data)
    elif data["type"] == GraphType.BAR.value:
        graph = BarGraph(**data)
    elif data["type"] == GraphType.PIE.value:
        graph = PieGraph(**data)
    elif data["type"] == GraphType.BOX_AND_WHISKER.value:
        graph = BoxAndWhiskerGraph(**data)
    elif data["type"] == GraphType.SUPERGRAPH.value:
        graph = SuperGraph(**data)
    else:
        graph = Graph(**data, type=GraphType.UNKNOWN)

    return graph
