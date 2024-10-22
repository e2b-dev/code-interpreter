import matplotlib.pyplot as plt

from e2b_data_extraction import graph_figure_to_graph
from e2b_data_extraction.graphs import Graph, GraphType


def _prep_graph_figure():
    # Create a figure and an axis
    fig, ax = plt.subplots()

    # Create data for two concentric circles
    circle1 = plt.Circle((0, 0), 1, color="blue", fill=False, linewidth=2)
    circle2 = plt.Circle((0, 0), 2, color="red", fill=False, linewidth=2)

    # Add the circles to the axes
    ax.add_artist(circle1)
    ax.add_artist(circle2)

    # Set grid
    ax.grid(True)

    # Set title
    plt.title("Two Concentric Circles")

    return plt.gcf()


def test_unknown_graphs():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, Graph)
    assert graph.type == GraphType.UNKNOWN
    assert graph.title == "Two Concentric Circles"

    assert len(graph.elements) == 0
