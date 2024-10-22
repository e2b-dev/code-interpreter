import numpy as np
import matplotlib.pyplot as plt
import datetime

from e2b_data_extraction import graph_figure_to_graph
from e2b_data_extraction.graphs import LineGraph


def _prep_graph_figure():
    x = [1, 2, 3, 4, 5]
    y = ["A", "B", "C", "D", "E"]

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(x, y)

    return plt.gcf()


def test_categorical_scale():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, LineGraph)
    assert graph.x_scale == "linear"
    assert graph.y_scale == "categorical"
