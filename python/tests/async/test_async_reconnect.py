from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


async def test_reconnect(async_sandbox: AsyncCodeInterpreter):
    sandbox_id = async_sandbox.sandbox_id

    sandbox2 = await AsyncCodeInterpreter.connect(sandbox_id)
    result = await sandbox2.notebook.exec_cell("x =1; x")
    assert result.text == "1"
