from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


async def test_stateful(async_sandbox: AsyncCodeInterpreter):
    await async_sandbox.notebook.exec_cell("async_test_stateful = 1")

    result = await async_sandbox.notebook.exec_cell(
        "async_test_stateful+=1; async_test_stateful"
    )
    assert result.text == "2"
