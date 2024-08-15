from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_env_vars():
    sbx = CodeInterpreter(envs={"FOO": "bar"})
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')")
    assert result.text == "bar"
    sbx.kill()


def test_env_vars_in_new_context():
    sbx = CodeInterpreter(envs={"FOO": "bar"})
    context_id = sbx.notebook.create_kernel()
    result = sbx.notebook.exec_cell("import os; os.getenv('FOO')", kernel_id=context_id)
    assert result.text == "bar"
    sbx.kill()
