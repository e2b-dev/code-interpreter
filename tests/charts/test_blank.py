from harness import CodeInterpreter


def test_blank_chart(client: CodeInterpreter):
    execution = client.run_code(
        """
        import matplotlib.pyplot as plt

        plt.subplots()
        plt.show()
        """
    )

    assert execution.error is None, execution.error
    assert len(execution.results) == 1
    assert execution.results[0].png
    assert execution.results[0].chart == {}
