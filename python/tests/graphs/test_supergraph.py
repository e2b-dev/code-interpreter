from e2b_code_interpreter.code_interpreter_async import AsyncSandbox
from e2b_code_interpreter.graphs import GraphType, SuperGraph, LineGraph, ScatterGraph

code = """
import matplotlib.pyplot as plt
import numpy as np

# Data for plotting
x1 = np.linspace(0, 10, 100)
y1 = np.sin(x1)

# Create a figure with multiple subplots
fig, axs = plt.subplots(1, 2, figsize=(10, 8))
fig.suptitle('Multiple Graphs Example', fontsize=16)

# Plotting on the different axes
axs[0].plot(x1, y1, 'r')
axs[0].set_title('Sine Wave')
axs[0].grid(True)

N = 5
x2 = np.random.rand(N)
y2 = np.random.rand(N)

axs[1].scatter(x2, y2, c='blue', label='Dataset 1')
axs[1].set_xlabel('X')
axs[1].set_ylabel('Y')
axs[1].set_title('Scatter Plot')
axs[1].grid(True)

plt.show()
"""


async def test_super_graph(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(code)
    graph = result.results[0].graph
    assert graph

    assert isinstance(graph, SuperGraph)
    assert graph.type == GraphType.SUPERGRAPH
    assert graph.title == "Multiple Graphs Example"

    graphs = graph.elements
    assert len(graphs) == 2

    first_graph = graphs[0]
    assert first_graph.title == "Sine Wave"
    assert isinstance(first_graph, LineGraph)
    assert first_graph.x_label is None
    assert first_graph.y_label is None
    assert len(first_graph.elements) == 1
    assert len(first_graph.elements[0].points) == 100

    second_graph = graphs[1]
    assert second_graph.title == "Scatter Plot"
    assert isinstance(second_graph, ScatterGraph)
    assert second_graph.x_label == "X"
    assert second_graph.y_label == "Y"
    assert len(second_graph.elements) == 1
    assert len(second_graph.elements[0].points) == 5
