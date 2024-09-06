from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


code = """
import matplotlib.pyplot as plt
import numpy as np

# Create data
N = 5
x1 = np.random.rand(N)
y1 = np.random.rand(N)
x2 = np.random.rand(2*N)
y2 = np.random.rand(2*N)

plt.xlabel("A")
plt.ylabel("B")

plt.scatter(x1, y1, c='blue', label='Dataset 1')
plt.scatter(x2, y2, c='red', label='Dataset 2')

plt.show()
"""


async def test_scatter_plot(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    data = result.results[0].data
    assert data

    graphs = data.get("graphs")
    assert graphs

    assert graphs[0]['type'] == "scatter"

    assert graphs[0]['x_label'] == "A"
    assert graphs[0]['y_label'] == "B"

    assert all(isinstance(x, float) for x in graphs[0]['x_ticks'])
    assert all(isinstance(y, float) for y in graphs[0]['y_ticks'])

    assert all(isinstance(x, str) for x in graphs[0]['y_tick_labels'])
    assert all(isinstance(y, str) for y in graphs[0]['y_tick_labels'])

    assert len(graphs[0]['data']) == 2

    first_data = graphs[0]['data'][0]
    assert first_data['label'] == 'Dataset 1'
    assert len(first_data['x']) == 5
    assert len(first_data['y']) == 5
    assert all(isinstance(x, float) for x in first_data['x'])
    assert all(isinstance(y, float) for y in first_data['y'])

    second_data = graphs[0]['data'][1]
    assert second_data['label'] == 'Dataset 2'
    assert len(second_data['x']) == 10
    assert len(second_data['y']) == 10
    assert all(isinstance(x, float) for x in second_data['x'])
    assert all(isinstance(y, float) for y in second_data['y'])
