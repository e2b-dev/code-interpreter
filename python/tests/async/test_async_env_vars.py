from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


async def test_env_vars_sandbox():
    sbx = await AsyncCodeInterpreter.create(envs={"FOO": "bar"})
    result = await sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"
    await sbx.kill()


async def test_env_vars_in_exec_cell(async_sandbox: AsyncCodeInterpreter):
    result = await async_sandbox.notebook.exec_cell(
        "import os; os.getenv('FOO')", envs={"FOO": "bar"}
    )
    assert result.text == "bar"


async def test_env_vars_override(debug: bool):
    sbx = await AsyncCodeInterpreter.create(envs={"FOO": "bar", "SBX": "value"})
    await sbx.notebook.exec_cell(
        "import os; os.environ['FOO'] = 'bar'; os.environ['RUNTIME_ENV'] = 'value'"
    )
    result = await sbx.notebook.exec_cell(
        "import os; os.getenv('FOO')", envs={"FOO": "baz"}
    )
    assert result.text == "baz"

    result = await sbx.notebook.exec_cell("import os; os.getenv('RUNTIME_ENV')")
    assert result.text == "value"

    if not debug:
        result = await sbx.notebook.exec_cell("import os; os.getenv('SBX')")
        assert result.text == "value"

    result = await sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"

    await sbx.kill()
