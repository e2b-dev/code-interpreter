from datetime import date
import enum
import re
from typing import Optional, List, Tuple, Literal, Any, Union, Sequence

import matplotlib
import numpy
import pandas
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Wedge, PathPatch
from matplotlib.pyplot import Figure
from matplotlib.dates import _SwitchableDateConverter
import IPython

from IPython.core.formatters import BaseFormatter
from matplotlib.text import Text
from pydantic import BaseModel, Field, field_validator
from traitlets.traitlets import Unicode, ObjectName


def _is_grid_line(line: Line2D) -> bool:
    x_data = line.get_xdata()
    if len(x_data) != 2:
        return False

    y_data = line.get_ydata()
    if len(y_data) != 2:
        return False

    if x_data[0] == x_data[1] or y_data[0] == y_data[1]:
        return True

    return False


class ChartType(str, enum.Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    PIE = "pie"
    BOX_AND_WHISKER = "box_and_whisker"
    SUPERCHART = "superchart"
    UNKNOWN = "unknown"


class Chart(BaseModel):
    type: ChartType
    title: Optional[str] = None

    elements: List[Any] = Field(default_factory=list)

    def __init__(self, ax: Optional[Axes] = None, **kwargs):
        super().__init__(**kwargs)
        if ax:
            self._extract_info(ax)

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for Chart
        """
        title = ax.get_title()
        if title == "":
            title = None

        self.title = title


class Chart2D(Chart):
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_unit: Optional[str] = None
    y_unit: Optional[str] = None

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for Chart2D
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
    points: List[Tuple[Union[str, float], Union[str, float]]]

    @field_validator("points", mode="before")
    @classmethod
    def transform_points(
        cls, value
    ) -> List[Tuple[Union[str, float], Union[str, float]]]:
        parsed_value = []
        for x, y in value:
            if isinstance(x, date):
                x = x.isoformat()
            if isinstance(x, numpy.datetime64):
                x = x.astype("datetime64[s]").astype(str)

            if isinstance(y, date):
                y = y.isoformat()
            if isinstance(y, numpy.datetime64):
                y = y.astype("datetime64[s]").astype(str)

            parsed_value.append((x, y))
        return parsed_value


class PointChart(Chart2D):
    x_ticks: List[Union[str, float]] = Field(default_factory=list)
    x_tick_labels: List[str] = Field(default_factory=list)
    x_scale: str = Field(default="linear")

    y_ticks: List[Union[str, float]] = Field(default_factory=list)
    y_tick_labels: List[str] = Field(default_factory=list)
    y_scale: str = Field(default="linear")

    elements: List[PointData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        """
        Function to extract information for PointChart
        """
        super()._extract_info(ax)

        self.x_tick_labels = [label.get_text() for label in ax.get_xticklabels()]

        x_ticks = ax.get_xticks()
        self.x_ticks = self._extract_ticks_info(ax.xaxis.converter, x_ticks)
        self.x_scale = self._detect_scale(
            ax.xaxis.converter, ax.get_xscale(), self.x_ticks, self.x_tick_labels
        )

        self.y_tick_labels = [label.get_text() for label in ax.get_yticklabels()]
        self.y_ticks = self._extract_ticks_info(ax.yaxis.converter, ax.get_yticks())
        self.y_scale = self._detect_scale(
            ax.yaxis.converter, ax.get_yscale(), self.y_ticks, self.y_tick_labels
        )

    @staticmethod
    def _detect_scale(converter, scale: str, ticks: Sequence, labels: Sequence) -> str:
        # If the converter is a date converter, it's a datetime scale
        if isinstance(converter, _SwitchableDateConverter):
            return "datetime"

        # If the scale is not linear, it can't be categorical
        if scale != "linear":
            return scale

        # If all the ticks are integers and are in order from 0 to n-1
        # and the labels aren't corresponding to the ticks, it's categorical
        for i, tick_and_label in enumerate(zip(ticks, labels)):
            tick, label = tick_and_label
            if isinstance(tick, (int, float)) and tick == i and str(i) != label:
                continue
            # Found a tick, which wouldn't be in a categorical scale
            return "linear"

        return "categorical"

    @staticmethod
    def _extract_ticks_info(converter: Any, ticks: Sequence) -> list:
        if isinstance(converter, _SwitchableDateConverter):
            return [matplotlib.dates.num2date(tick).isoformat() for tick in ticks]
        else:
            example_tick = ticks[0]

            if isinstance(example_tick, (int, float)):
                return [float(tick) for tick in ticks]
            else:
                return list(ticks)


class LineChart(PointChart):
    type: Literal[ChartType.LINE] = ChartType.LINE

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        for line in ax.get_lines():
            if _is_grid_line(line):
                continue
            label = line.get_label()
            if label.startswith("_child"):
                number = int(label[6:])
                label = f"Line {number}"

            points = [(x, y) for x, y in zip(line.get_xdata(), line.get_ydata())]
            line_data = PointData(label=label, points=points)
            self.elements.append(line_data)


class ScatterChart(PointChart):
    type: Literal[ChartType.SCATTER] = ChartType.SCATTER

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


class BarChart(Chart2D):
    type: Literal[ChartType.BAR] = ChartType.BAR

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


class PieChart(Chart):
    type: Literal[ChartType.PIE] = ChartType.PIE

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


class BoxAndWhiskerChart(Chart2D):
    type: Literal[ChartType.BOX_AND_WHISKER] = ChartType.BOX_AND_WHISKER

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


class SuperChart(Chart):
    type: Literal[ChartType.SUPERCHART] = ChartType.SUPERCHART
    elements: List[
        LineChart | ScatterChart | BarChart | PieChart | BoxAndWhiskerChart
    ] = Field(default_factory=list)

    def __init__(self, figure: Figure):
        title = figure.get_suptitle()
        super().__init__(title=title)

        self.elements = [get_chart_from_ax(ax) for ax in figure.axes]


def _get_type_of_chart(ax: Axes) -> ChartType:
    objects = list(filter(lambda obj: not isinstance(obj, Text), ax._children))

    # Check for Line plots
    if all(isinstance(line, Line2D) for line in objects):
        return ChartType.LINE

    if all(isinstance(box_or_path, (PathPatch, Line2D)) for box_or_path in objects):
        return ChartType.BOX_AND_WHISKER

    filtered = []
    for obj in objects:
        if isinstance(obj, Line2D) and _is_grid_line(obj):
            continue
        filtered.append(obj)

    objects = filtered

    # Check for Scatter plots
    if all(isinstance(path, PathCollection) for path in objects):
        return ChartType.SCATTER

    # Check for Pie plots
    if all(isinstance(artist, Wedge) for artist in objects):
        return ChartType.PIE

    # Check for Bar plots
    if all(isinstance(rect, Rectangle) for rect in objects):
        return ChartType.BAR

    return ChartType.UNKNOWN


def get_chart_from_ax(
    ax: Axes,
) -> LineChart | ScatterChart | BarChart | PieChart | BoxAndWhiskerChart | Chart:
    chart_type = _get_type_of_chart(ax)

    if chart_type == ChartType.LINE:
        chart = LineChart(ax=ax)
    elif chart_type == ChartType.SCATTER:
        chart = ScatterChart(ax=ax)
    elif chart_type == ChartType.BAR:
        chart = BarChart(ax=ax)
    elif chart_type == ChartType.PIE:
        chart = PieChart(ax=ax)
    elif chart_type == ChartType.BOX_AND_WHISKER:
        chart = BoxAndWhiskerChart(ax=ax)
    else:
        chart = Chart(ax=ax, type=chart_type)

    return chart


def _figure_repr_e2b_chart_(self: Figure):
    """
    This method is used to extract data from the figure object to a dictionary
    """
    # Get all Axes objects from the Figure
    axes = self.get_axes()

    try:
        if not axes:
            return {}
        elif len(axes) > 1:
            chart = SuperChart(figure=self)
        else:
            ax = axes[0]
            chart = get_chart_from_ax(ax)
        return chart.model_dump()
    except:
        return {}


def _dataframe_repr_e2b_data_(self: pandas.DataFrame):
    return self.to_dict(orient="list")


class E2BDataFormatter(BaseFormatter):
    format_type = Unicode("e2b/data")

    print_method = ObjectName("_repr_e2b_data_")
    _return_type = (dict, str)

    type_printers = {pandas.DataFrame: _dataframe_repr_e2b_data_}


class E2BChartFormatter(BaseFormatter):
    format_type = Unicode("e2b/chart")

    print_method = ObjectName("_repr_e2b_chart_")
    _return_type = (dict, str)

    def __call__(self, obj):
        # Figure object is for some reason removed on execution of the cell,
        # so it can't be used in type_printers or with top-level import
        from matplotlib.pyplot import Figure

        if isinstance(obj, Figure):
            return _figure_repr_e2b_chart_(obj)
        return super().__call__(obj)


ip = IPython.get_ipython()
ip.display_formatter.formatters["e2b/data"] = E2BDataFormatter(
    parent=ip.display_formatter
)
ip.display_formatter.formatters["e2b/chart"] = E2BChartFormatter(
    parent=ip.display_formatter
)
