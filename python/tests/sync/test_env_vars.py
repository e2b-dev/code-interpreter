from e2b_code_interpreter.code_interpreter_sync import Sandbox


async def test_env_vars_sandbox():
    sbx = Sandbox(envs={"FOO": "bar"})
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"
    sbx.kill()


async def test_env_vars_in_exec_cell(sandbox: Sandbox):
    result = sandbox.notebook.exec_cell(
        "import os; os.getenv('FOO')", envs={"FOO": "bar"}
    )
    assert result.text == "bar"


async def test_env_vars_override(debug: bool):
    sbx = Sandbox(envs={"FOO": "bar", "SBX": "value"})
    sbx.notebook.exec_cell(
        "import os; os.environ['FOO'] = 'bar'; os.environ['RUNTIME_ENV'] = 'python_runtime'"
    )
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')", envs={"FOO": "baz"})
    assert result.text == "baz"

    # This can fail if running in debug mode (there's a race condition with the restart kernel test)
    result = sbx.notebook.exec_cell("import os; os.getenv('RUNTIME_ENV')")
    assert result.text == "python_runtime"

    if not debug:
        result = sbx.notebook.exec_cell("import os; os.getenv('SBX')")
        assert result.text == "value"

    # This can fail if running in debug mode (there's a race condition with the restart kernel test)
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"

    sbx.kill()
