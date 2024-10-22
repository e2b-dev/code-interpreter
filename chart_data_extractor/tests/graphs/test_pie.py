import matplotlib.pyplot as plt

from e2b_data_extraction import graph_figure_to_graph
from e2b_data_extraction.graphs import PieGraph


def _prep_graph_figure():
    # Step 1: Define the data for the pie chart
    categories = ["No", "No, in blue"]
    sizes = [90, 10]

    # Step 2: Create the figure and axis objects
    fig, ax = plt.subplots(figsize=(8, 8))

    plt.xlabel("x")
    plt.ylabel("y")

    # Step 3: Create the pie chart
    ax.pie(
        sizes,
        labels=categories,
        autopct="%1.1f%%",
        startangle=90,
        colors=plt.cm.Pastel1.colors[: len(categories)],
    )

    # Step 4: Add title and legend
    ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title("Will I wake up early tomorrow?")

    return plt.gcf()


def test_pie_graph():
    figure = _prep_graph_figure()
    graph = graph_figure_to_graph(figure)
    assert graph

    assert isinstance(graph, PieGraph)

    assert graph.title == "Will I wake up early tomorrow?"

    assert len(graph.elements) == 2

    first_data = graph.elements[0]
    assert first_data.label == "No"
    assert first_data.angle == 324
    assert first_data.radius == 1

    second_data = graph.elements[1]
    assert second_data.label == "No, in blue"
    assert second_data.angle == 36
    assert second_data.radius == 1
