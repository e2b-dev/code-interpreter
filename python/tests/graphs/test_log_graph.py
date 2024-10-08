from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter
from e2b_code_interpreter.graphs import LineGraph

# Log graph
code = """
import numpy as np
import matplotlib.pyplot as plt

# Generate x values
x = np.linspace(0, 100, 100)
# Calculate y values
y = np.exp(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='y = e^x')

# Set log scale for the y-axis
plt.yscale('log')

# Add labels and title
plt.xlabel('X-axis')
plt.ylabel('Y-axis (log scale)')
plt.title('Graph with Log Scale on Y-axis')

plt.legend()
plt.grid(True)
plt.show()
"""


async def test_log_graph(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    graph = result.results[0].graph
    assert graph

    assert isinstance(graph, LineGraph)
    assert graph.title == "Graph with Log Scale on Y-axis"

    assert graph.x_label == "X-axis"
    assert graph.y_label == "Y-axis (log scale)"

    assert graph.x_unit == None
    assert graph.y_unit == "log scale"

    assert graph.x_scale == "linear"
    assert graph.y_scale == "log"

    assert all(isinstance(x, float) for x in graph.x_ticks)
    assert all(isinstance(y, float) for y in graph.y_ticks)

    assert all(isinstance(x, str) for x in graph.x_tick_labels)
    assert all(isinstance(y, str) for y in graph.y_tick_labels)

    lines = graph.elements
    assert len(lines) == 1

    line = lines[0]
    assert line.label == "y = e^x"
    assert len(line.points) == 100

    assert all(isinstance(x, tuple) for x in line.points)
    assert all(isinstance(x, float) and isinstance(y, float) for x, y in line.points)
