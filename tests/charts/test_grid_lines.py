def test_grid_lines_are_not_chart_elements(run_chart):
    chart = run_chart(
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        plt.plot([1, 2], [2, 3], label='two points')
        plt.plot([1, 2, 3, 4], [2, 2, 2, 2], label='flat')
        plt.axhline(2.5)
        plt.axvline(1.5)
        plt.grid(True)
        plt.show()
        """
    )

    assert chart["type"] == "line"
    assert [line["label"] for line in chart["elements"]] == ["two points", "flat"]
