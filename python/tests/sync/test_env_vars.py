from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


async def test_env_vars_sandbox():
    sbx = CodeInterpreter(envs={"FOO": "bar"})
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"
    sbx.kill()


async def test_env_vars_in_exec_cell(sandbox: CodeInterpreter):
    result = sandbox.notebook.exec_cell("import os; os.getenv('FOO')", envs={"FOO": "bar"})
    assert result.text == "bar"


async def test_env_vars_override():
    sbx = CodeInterpreter(envs={"FOO": "bar", "SBX": "value"})
    sbx.notebook.exec_cell("import os; os.environ['FOO'] = 'baz'; os.environ['RUNTIME_ENV'] = 'value'")
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')", envs={"FOO": "baz"})
    assert result.text == "baz"

    result = sbx.notebook.exec_cell("import os; os.getenv('RUNTIME_ENV')")
    assert result.text == "value"

    result = sbx.notebook.exec_cell("import os; os.getenv('SBX')")
    assert result.text == "value"

    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"

    sbx.kill()
