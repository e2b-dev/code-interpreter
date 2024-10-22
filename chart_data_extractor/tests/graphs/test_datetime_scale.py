import numpy as np
import matplotlib.pyplot as plt
import datetime

from e2b_data_extraction import graph_figure_to_graph
from e2b_data_extraction.graphs import LineGraph


def _prep_graph_figure():
    # Generate x values
    dates = [
        datetime.date(2023, 9, 1) + datetime.timedelta(seconds=i) for i in range(100)
    ]
    y_sin = np.sin(np.linspace(0, 2 * np.pi, 100))

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, y_sin, label="sin(x)")

    return plt.gcf()


def test_datetime_scale():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, LineGraph)
    assert graph.x_scale == "datetime"
    assert graph.y_scale == "linear"
