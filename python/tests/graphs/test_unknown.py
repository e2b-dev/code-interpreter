from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter
from e2b_code_interpreter.graphs import GraphType, Graph

code = """
import matplotlib.pyplot as plt
import numpy as np

# Create a figure and an axis
fig, ax = plt.subplots()

# Create data for two concentric circles
circle1 = plt.Circle((0, 0), 1, color='blue', fill=False, linewidth=2)
circle2 = plt.Circle((0, 0), 2, color='red', fill=False, linewidth=2)

# Add the circles to the axes
ax.add_artist(circle1)
ax.add_artist(circle2)

# Set grid
ax.grid(True)

# Set title
plt.title('Two Concentric Circles')

# Show the plot
plt.show()
"""


async def test_unknown_graphs(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    graph = result.results[0].graph
    assert graph

    assert isinstance(graph, Graph)
    assert graph.type == GraphType.UNKNOWN
    assert graph.title == "Two Concentric Circles"

    assert len(graph.elements) == 0
