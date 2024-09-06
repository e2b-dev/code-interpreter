from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter

code = """
import numpy as np
import matplotlib.pyplot as plt

# Generate x values
x = np.linspace(0, 2*np.pi, 100)

# Calculate y values
y_sin = np.sin(x)
y_cos = np.cos(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y_sin, label='sin(x)')
plt.plot(x, y_cos, label='cos(x)')

# Add labels and title
plt.xlabel('x')
plt.ylabel('y')
plt.title('Plot of sin(x) and cos(x)')

# Display the plot
plt.show()
"""


async def test_scatter_plot(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    data = result.results[0].data
    assert data

    graphs = data.get("graphs")
    assert graphs

    assert graphs[0]['type'] == "line"
    assert graphs[0]['title'] == "Plot of sin(x) and cos(x)"
    assert graphs[0]['x_label'] == "x"
    assert graphs[0]['y_label'] == "y"

    assert all(isinstance(x, float) for x in graphs[0]['x_ticks'])
    assert all(isinstance(y, float) for y in graphs[0]['y_ticks'])

    assert all(isinstance(x, str) for x in graphs[0]['y_tick_labels'])
    assert all(isinstance(y, str) for y in graphs[0]['y_tick_labels'])

    assert len(graphs[0]['data']) == 2

    first_data = graphs[0]['data'][0]
    assert first_data['label'] == 'sin(x)'
    assert len(first_data['x']) == 100
    assert len(first_data['y']) == 100
    assert all(isinstance(x, float) for x in first_data['x'])
    assert all(isinstance(y, float) for y in first_data['y'])

    second_data = graphs[0]['data'][1]
    assert second_data['label'] == 'cos(x)'
    assert len(second_data['x']) == 100
    assert len(second_data['y']) == 100
    assert all(isinstance(x, float) for x in second_data['x'])
    assert all(isinstance(y, float) for y in second_data['y'])
