import pytest_asyncio

from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter

@pytest_asyncio.fixture
async def test_bash(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell("!pwd")
    assert "".join(result.logs.stdout).strip() == "/home/user"
