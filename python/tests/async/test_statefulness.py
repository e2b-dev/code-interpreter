import pytest_asyncio

from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


@pytest_asyncio.fixture
async def test_stateful(async_sandbox: AsyncCodeInterpreter):
    await async_sandbox.notebook.exec_cell("x = 1")

    result = await async_sandbox.notebook.exec_cell("x+=1; x")
    assert result.text == "2"
