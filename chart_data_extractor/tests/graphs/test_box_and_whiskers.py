import matplotlib.pyplot as plt

from e2b_data_extraction import graph_figure_to_graph
from e2b_data_extraction.graphs import BoxAndWhiskerGraph, GraphType


def _prep_graph_figure():
    # Sample data
    data = {
        "Class A": [85, 90, 78, 92, 88],
        "Class B": [95, 89, 76, 91, 84, 87],
        "Class C": [75, 82, 88, 79, 86],
    }

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot box plot
    ax.boxplot(data.values(), tick_labels=data.keys())

    # Customize plot
    ax.set_title("Exam Scores Distribution")
    ax.set_xlabel("Class")
    ax.set_ylabel("Score")

    # Set custom colors
    ax.boxplot(data.values(), tick_labels=data.keys(), patch_artist=True)

    # Adjust layout and show plot
    plt.tight_layout()
    return plt.gcf()


def test_box_and_whiskers():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, BoxAndWhiskerGraph)
    assert graph.type == GraphType.BOX_AND_WHISKER
    assert graph.title == "Exam Scores Distribution"

    assert graph.x_label == "Class"
    assert graph.y_label == "Score"

    assert graph.x_unit is None
    assert graph.y_unit is None

    bars = graph.elements
    assert len(bars) == 3

    assert all(isinstance(bar.min, float) for bar in bars)
    assert all(isinstance(bar.first_quartile, float) for bar in bars)
    assert all(isinstance(bar.median, float) for bar in bars)
    assert all(isinstance(bar.third_quartile, float) for bar in bars)
    assert all(isinstance(bar.max, float) for bar in bars)
    assert all(isinstance(bar.label, str) for bar in bars)
