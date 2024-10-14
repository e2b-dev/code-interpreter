from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_basic(async_sandbox: AsyncSandbox):
    result = await async_sandbox.notebook.exec_cell("x =1; x")
    assert result.text == "1"
