import enum
import re
from typing import Optional, List, Tuple, Literal, Any

import pandas
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Wedge, PathPatch
from matplotlib.pyplot import Figure
import IPython

from IPython.core.formatters import BaseFormatter
from matplotlib.text import Text
from pydantic import BaseModel, Field
from traitlets.traitlets import Unicode, ObjectName


class GraphType(str, enum.Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    PIE = "pie"
    BOX_AND_WHISKER = "box_and_whisker"
    SUPERGRAPH = "supergraph"
    UNKNOWN = "unknown"


class Graph(BaseModel):
    type: GraphType
    title: Optional[str] = None

    elements: List[Any] = Field(default_factory=list)

    def __init__(self, ax: Optional[Axes] = None, **kwargs):
        super().__init__(**kwargs)
        if ax:
            self._extract_info(ax)

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for Graph
        """
        title = ax.get_title()
        if title == "":
            title = None

        self.title = title


class Graph2D(Graph):
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_unit: Optional[str] = None
    y_unit: Optional[str] = None

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for Graph2D
        """
        super()._extract_info(ax)
        x_label = ax.get_xlabel()
        if x_label == "":
            x_label = None
        self.x_label = x_label

        y_label = ax.get_ylabel()
        if y_label == "":
            y_label = None
        self.y_label = y_label

        regex = r"\s\((.*?)\)|\[(.*?)\]"
        if self.x_label:
            match = re.search(regex, self.x_label)
            if match:
                self.x_unit = match.group(1) or match.group(2)

        if self.y_label:
            match = re.search(regex, self.y_label)
            if match:
                self.y_unit = match.group(1) or match.group(2)

    def _change_orientation(self):
        self.x_label, self.y_label = self.y_label, self.x_label
        self.x_unit, self.y_unit = self.y_unit, self.x_unit


class PointData(BaseModel):
    label: str
    points: List[Tuple[float, float]]


class PointGraph(Graph2D):
    x_ticks: List[float] = Field(default_factory=list)
    x_tick_labels: List[str] = Field(default_factory=list)
    y_ticks: List[float] = Field(default_factory=list)
    y_tick_labels: List[str] = Field(default_factory=list)

    elements: List[PointData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for PointGraph
        """
        super()._extract_info(ax)
        self.x_ticks = [float(tick) for tick in ax.get_xticks()]
        self.x_tick_labels = [label.get_text() for label in ax.get_xticklabels()]

        self.y_ticks = [float(tick) for tick in ax.get_yticks()]
        self.y_tick_labels = [label.get_text() for label in ax.get_yticklabels()]


class LineGraph(PointGraph):
    type: Literal[GraphType.LINE] = GraphType.LINE

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        for line in ax.get_lines():
            label = line.get_label()
            if label.startswith("_child"):
                number = int(label[6:])
                label = f"Line {number}"

            points = [(x, y) for x, y in zip(line.get_xdata(), line.get_ydata())]
            line_data = PointData(label=label, points=points)
            self.elements.append(line_data)


class ScatterGraph(PointGraph):
    type: Literal[GraphType.SCATTER] = GraphType.SCATTER

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        for collection in ax.collections:
            points = [(x, y) for x, y in collection.get_offsets()]
            scatter_data = PointData(label=collection.get_label(), points=points)
            self.elements.append(scatter_data)


class BarData(BaseModel):
    label: str
    group: str
    value: float


class BarGraph(Graph2D):
    type: Literal[GraphType.BAR] = GraphType.BAR

    elements: List[BarData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)
        for container in ax.containers:
            group_label = container.get_label()
            if group_label.startswith("_container"):
                number = int(group_label[10:])
                group_label = f"Group {number}"

            heights = [rect.get_height() for rect in container]
            if all(height == heights[0] for height in heights):
                # vertical bars
                self._change_orientation()
                labels = [label.get_text() for label in ax.get_yticklabels()]
                values = [rect.get_width() for rect in container]
            else:
                # horizontal bars
                labels = [label.get_text() for label in ax.get_xticklabels()]
                values = heights
            for label, value in zip(labels, values):

                bar = BarData(label=label, value=value, group=group_label)
                self.elements.append(bar)


class PieData(BaseModel):
    label: str
    angle: float
    radius: float


class PieGraph(Graph):
    type: Literal[GraphType.PIE] = GraphType.PIE

    elements: List[PieData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        for wedge in ax.patches:
            pie_data = PieData(
                label=wedge.get_label(),
                angle=abs(round(wedge.theta2 - wedge.theta1, 4)),
                radius=wedge.r,
            )

            self.elements.append(pie_data)


class BoxAndWhiskerData(BaseModel):
    label: str
    min: float
    first_quartile: float
    median: float
    third_quartile: float
    max: float


class BoxAndWhiskerGraph(Graph2D):
    type: Literal[GraphType.BOX_AND_WHISKER] = GraphType.BOX_AND_WHISKER

    elements: List[BoxAndWhiskerData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        boxes = []
        for box in ax.patches:
            vertices = box.get_path().vertices
            x_vertices = vertices[:, 0]
            y_vertices = vertices[:, 1]
            x = min(x_vertices)
            y = min(y_vertices)
            boxes.append(
                {
                    "x": x,
                    "y": y,
                    "label": box.get_label(),
                    "width": round(max(x_vertices) - x, 4),
                    "height": round(max(y_vertices) - y, 4),
                }
            )

        orientation = "horizontal"
        if all(box["height"] == boxes[0]["height"] for box in boxes):
            orientation = "vertical"

        if orientation == "vertical":
            self._change_orientation()
            for box in boxes:
                box["x"], box["y"] = box["y"], box["x"]
                box["width"], box["height"] = box["height"], box["width"]

        for line in ax.lines:
            xdata = line.get_xdata()
            ydata = line.get_ydata()

            if orientation == "vertical":
                xdata, ydata = ydata, xdata

            if len(ydata) != 2:
                continue
            for box in boxes:
                if box["x"] <= xdata[0] <= xdata[1] <= box["x"] + box["width"]:
                    break
            else:
                continue

            if (
                ydata[0] == ydata[1]
                and box["y"] <= ydata[0] <= box["y"] + box["height"]
            ):
                box["median"] = ydata[0]
                continue

            lower_value = min(ydata)
            upper_value = max(ydata)
            if upper_value == box["y"]:
                box["whisker_lower"] = lower_value
            elif lower_value == box["y"] + box["height"]:
                box["whisker_upper"] = upper_value

        self.elements = [
            BoxAndWhiskerData(
                label=box["label"],
                min=box["whisker_lower"],
                first_quartile=box["y"],
                median=box["median"],
                third_quartile=box["y"] + box["height"],
                max=box["whisker_upper"],
            )
            for box in boxes
        ]


class SuperGraph(Graph):
    type: Literal[GraphType.SUPERGRAPH] = GraphType.SUPERGRAPH
    elements: List[
        LineGraph | ScatterGraph | BarGraph | PieGraph | BoxAndWhiskerGraph
    ] = Field(default_factory=list)

    def __init__(self, figure: Figure):
        title = figure.get_suptitle()
        super().__init__(title=title)

        self.elements = [get_graph_from_ax(ax) for ax in figure.axes]


def _get_type_of_graph(ax: Axes) -> GraphType:
    objects = list(filter(lambda obj: not isinstance(obj, Text), ax._children))

    # Check for Line plots
    if all(isinstance(line, Line2D) for line in objects):
        return GraphType.LINE

    # Check for Scatter plots
    if all(isinstance(path, PathCollection) for path in objects):
        return GraphType.SCATTER

    # Check for Pie plots
    if all(isinstance(artist, Wedge) for artist in objects):
        return GraphType.PIE

    # Check for Bar plots
    if all(isinstance(rect, Rectangle) for rect in objects):
        return GraphType.BAR

    if all(isinstance(box_or_path, (PathPatch, Line2D)) for box_or_path in objects):
        return GraphType.BOX_AND_WHISKER

    return GraphType.UNKNOWN


def get_graph_from_ax(
    ax: Axes,
) -> LineGraph | ScatterGraph | BarGraph | PieGraph | BoxAndWhiskerGraph | Graph:
    graph_type = _get_type_of_graph(ax)

    if graph_type == GraphType.LINE:
        graph = LineGraph(ax=ax)
    elif graph_type == GraphType.SCATTER:
        graph = ScatterGraph(ax=ax)
    elif graph_type == GraphType.BAR:
        graph = BarGraph(ax=ax)
    elif graph_type == GraphType.PIE:
        graph = PieGraph(ax=ax)
    elif graph_type == GraphType.BOX_AND_WHISKER:
        graph = BoxAndWhiskerGraph(ax=ax)
    else:
        graph = Graph(ax=ax, type=graph_type)

    return graph


def _figure_repr_e2b_graph_(self: Figure):
    """
    This method is used to extract data from the figure object to a dictionary
    """
    # Get all Axes objects from the Figure
    axes = self.get_axes()

    try:
        if not axes:
            return {}
        elif len(axes) > 1:
            graph = SuperGraph(figure=self)
        else:
            ax = axes[0]
            graph = get_graph_from_ax(ax)
        return graph.model_dump()
    except:
        return {}


def _dataframe_repr_e2b_data_(self: pandas.DataFrame):
    return self.to_dict(orient="list")


class E2BDataFormatter(BaseFormatter):
    format_type = Unicode("e2b/data")

    print_method = ObjectName("_repr_e2b_data_")
    _return_type = (dict, str)

    type_printers = {pandas.DataFrame: _dataframe_repr_e2b_data_}


class E2BGraphFormatter(BaseFormatter):
    format_type = Unicode("e2b/graph")

    print_method = ObjectName("_repr_e2b_data_")
    _return_type = (dict, str)

    def __call__(self, obj):
        # Figure object is for some reason removed on execution of the cell,
        # so it can't be used in type_printers or with top-level import
        from matplotlib.pyplot import Figure

        if isinstance(obj, Figure):
            return _figure_repr_e2b_graph_(obj)
        return super().__call__(obj)


ip = IPython.get_ipython()
ip.display_formatter.formatters["e2b/data"] = E2BDataFormatter(
    parent=ip.display_formatter
)
ip.display_formatter.formatters["e2b/graph"] = E2BGraphFormatter(
    parent=ip.display_formatter
)
