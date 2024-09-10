from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


code = """
import matplotlib.pyplot as plt

# Prepare data
authors = ['Author A', 'Author B', 'Author C', 'Author D']
sales = [100, 200, 300, 400]

# Create and customize the bar graph
plt.figure(figsize=(10, 6))
plt.bar(authors, sales)
plt.xlabel('Authors')
plt.ylabel('Number of Books Sold')
plt.title('Book Sales by Authors')

# Display the graph
plt.tight_layout()
plt.show()
"""


async def test_graph_bar(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    data = result.results[0].data
    assert data

    graphs = data.get("graphs")
    assert graphs

    assert graphs[0]['type'] == "bar"
    assert graphs[0]['title'] == "Book Sales by Authors"

    assert graphs[0]['x_label'] == "Authors"
    assert graphs[0]['y_label'] == "Number of Books Sold"

    assert graphs[0]['x_unit'] is None
    assert graphs[0]['y_unit'] is None

    assert all(isinstance(x, int) for x in graphs[0]['x_ticks'])
    assert all(isinstance(y, float) for y in graphs[0]['y_ticks'])

    assert all(isinstance(x, str) for x in graphs[0]['y_tick_labels'])
    assert all(isinstance(y, str) for y in graphs[0]['y_tick_labels'])

    assert len(graphs[0]['data']) == 1

    data = graphs[0]['data'][0]
    assert len(data['x']) == 4
    assert len(data['y']) == 4
    assert data['orientation'] == "horizontal"

    assert all(isinstance(x, (int, float)) for x in data['widths'])
    assert all(isinstance(x, (int, float)) for x in data['heights'])
    assert all(isinstance(y, (int, float)) for y in data['x'])
    assert all(isinstance(y, (int, float)) for y in data['y'])
