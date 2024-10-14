from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_bash(async_sandbox: AsyncSandbox):
    result = await async_sandbox.notebook.exec_cell("!pwd")
    assert "".join(result.logs.stdout).strip() == "/home/user"
