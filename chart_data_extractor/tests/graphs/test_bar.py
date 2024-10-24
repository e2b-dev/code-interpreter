import matplotlib.pyplot as plt

from e2b_charts import graph_figure_to_graph
from e2b_charts.graphs import BarGraph, GraphType


def _prep_graph_figure():
    # Prepare data
    authors = ["Author A", "Author B", "Author C", "Author D"]
    sales = [100, 200, 300, 400]

    # Create and customize the bar graph
    plt.figure(figsize=(10, 6))
    plt.bar(authors, sales, label="Books Sold", color="blue")
    plt.xlabel("Authors")
    plt.ylabel("Number of Books Sold")
    plt.title("Book Sales by Authors")

    # Display the graph
    plt.tight_layout()
    return plt.gcf()


def test_graph_bar():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, BarGraph)
    assert graph.type == GraphType.BAR
    assert graph.title == "Book Sales by Authors"

    assert graph.x_label == "Authors"
    assert graph.y_label == "Number of Books Sold"

    assert graph.x_unit is None
    assert graph.y_unit is None

    bars = graph.elements
    assert len(bars) == 4

    assert [bar.value for bar in bars] == [100, 200, 300, 400]
    assert [bar.label for bar in bars] == [
        "Author A",
        "Author B",
        "Author C",
        "Author D",
    ]
    assert [bar.group for bar in bars] == ["Books Sold"] * 4
