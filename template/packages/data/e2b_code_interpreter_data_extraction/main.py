from typing import Optional, List, Any, Literal

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Wedge, PathPatch
from matplotlib.pyplot import Figure

from matplotlib.text import Text
from pydantic import BaseModel, Field

from e2b_code_interpreter_data_extraction.graphs import (
    GraphType,
    Graph,
    LineGraph,
    BarGraph,
    BoxAndWhiskerGraph,
    PieGraph,
    ScatterGraph,
)
from e2b_code_interpreter_data_extraction.utils.filtering import is_grid_line


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

    if all(isinstance(box_or_path, (PathPatch, Line2D)) for box_or_path in objects):
        return GraphType.BOX_AND_WHISKER

    filtered = []
    for obj in objects:
        if isinstance(obj, Line2D) and is_grid_line(obj):
            continue
        filtered.append(obj)

    objects = filtered

    # Check for Scatter plots
    if all(isinstance(path, PathCollection) for path in objects):
        return GraphType.SCATTER

    # Check for Pie plots
    if all(isinstance(artist, Wedge) for artist in objects):
        return GraphType.PIE

    # Check for Bar plots
    if all(isinstance(rect, Rectangle) for rect in objects):
        return GraphType.BAR

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


def graph_figure_to_graph(figure: Figure) -> Optional[Graph]:
    """
    This method is used to extract data from the figure object to a dictionary
    """
    # Get all Axes objects from the Figure
    axes = figure.get_axes()

    if not axes:
        return
    elif len(axes) > 1:
        return SuperGraph(figure=figure)
    else:
        ax = axes[0]
        return get_graph_from_ax(ax)


def graph_figure_to_dict(figure: Figure) -> dict:
    graph = graph_figure_to_graph(figure)
    if graph:
        return graph.model_dump()
    return {}
