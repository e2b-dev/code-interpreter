from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter

code = """
import matplotlib.pyplot as plt
import numpy as np

# Step 1: Define the data for the pie chart
categories = ["No", "No, in blue"]
sizes = [90, 10] 

# Step 2: Create the figure and axis objects
fig, ax = plt.subplots(figsize=(8, 8))

plt.xlabel("x")
plt.ylabel("y")

# Step 3: Create the pie chart
ax.pie(sizes, labels=categories, autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel1.colors[:len(categories)])

# Step 4: Add title and legend
ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
plt.title('Will I wake up early tomorrow?')

# Step 5: Show the plot
plt.show()
"""


async def test_pie_graph(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(code)

    data = result.results[0].data
    assert data

    graphs = data.get("graphs")
    assert graphs

    assert graphs[0]['type'] == "pie"
    assert graphs[0]['title'] == "Will I wake up early tomorrow?"
    assert graphs[0]['x_label'] == "x"
    assert graphs[0]['y_label'] == "y"

    assert len(graphs[0]['x_ticks']) == 0
    assert len(graphs[0]['y_ticks']) == 0

    assert len(graphs[0]['data']) == 2

    first_data = graphs[0]['data'][0]
    assert first_data['label'] == 'No'
    assert round(first_data['theta']) == 324
    assert first_data['r'] == 1

    second_data = graphs[0]['data'][1]
    assert second_data['label'] == 'No, in blue'
    assert round(second_data['theta']) == 36
    assert second_data['r'] == 1
