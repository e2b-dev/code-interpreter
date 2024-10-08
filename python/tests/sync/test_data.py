from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_data(sandbox: CodeInterpreter):
    # plot random graph
    result = sandbox.notebook.exec_cell(
        """
        import pandas as pd
        pd.DataFrame({"a": [1, 2, 3]})
        """
    )

    # there's your image
    data = result.results[0]
    assert data.data
    assert "a" in data.data
    assert len(data.data["a"]) == 3
