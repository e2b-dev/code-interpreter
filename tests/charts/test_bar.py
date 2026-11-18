code = """
import matplotlib.pyplot as plt

# Prepare data
authors = ['Author A', 'Author B', 'Author C', 'Author D']
sales = [100, 200, 300, 400]

# Create and customize the bar chart
plt.figure(figsize=(10, 6))
plt.bar(authors, sales, label='Books Sold', color='blue')
plt.xlabel('Authors')
plt.ylabel('Number of Books Sold')
plt.title('Book Sales by Authors')

# Display the chart
plt.tight_layout()
plt.show()
"""


def test_chart_bar(run_chart):
    chart = run_chart(code)

    assert chart["type"] == "bar"
    assert chart["title"] == "Book Sales by Authors"

    assert chart["x_label"] == "Authors"
    assert chart["y_label"] == "Number of Books Sold"

    assert chart["x_unit"] is None
    assert chart["y_unit"] is None

    bars = chart["elements"]
    assert len(bars) == 4

    assert [bar["value"] for bar in bars] == [100, 200, 300, 400]
    assert [bar["label"] for bar in bars] == [
        "Author A",
        "Author B",
        "Author C",
        "Author D",
    ]
    assert [bar["group"] for bar in bars] == ["Books Sold"] * 4


code_with_yerr = """
import matplotlib.pyplot as plt

categories = ['A', 'B', 'C']
values = [10, 15, 7]
errors = [1.5, 2.0, 0.8]

plt.figure(figsize=(6, 4))
plt.bar(categories, values, yerr=errors, capsize=5, label='Measurement')
plt.xlabel('Category')
plt.ylabel('Value')
plt.title('Bar Plot with Error Bars')
plt.tight_layout()
plt.show()
"""


def test_chart_bar_with_error_bars(run_chart):
    chart = run_chart(code_with_yerr)

    assert chart["type"] == "bar"
    assert chart["title"] == "Bar Plot with Error Bars"
    assert chart["x_label"] == "Category"
    assert chart["y_label"] == "Value"

    bars = chart["elements"]
    assert len(bars) == 3
    assert [bar["value"] for bar in bars] == [10, 15, 7]
    assert [bar["label"] for bar in bars] == ["A", "B", "C"]
    assert [bar["group"] for bar in bars] == ["Measurement"] * 3
