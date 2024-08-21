from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


async def test_data(async_sandbox: AsyncCodeInterpreter):
    # plot random graph
    result = await async_sandbox.notebook.exec_cell(
        """
        pd.DataFrame({"a": [1, 2, 3]})
        """
    )

    # there's your image
    data = result.results[0]
    assert data.data
