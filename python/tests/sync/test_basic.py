from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_basic(sandbox: Sandbox):
    result = sandbox.notebook.exec_cell("x =1; x")
    assert result.text == "1"
