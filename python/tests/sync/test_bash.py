from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_bash(sandbox: Sandbox):
    result = sandbox.notebook.exec_cell("!pwd")
    assert "".join(result.logs.stdout).strip() == "/home/user"
