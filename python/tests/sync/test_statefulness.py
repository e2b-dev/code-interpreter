from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_stateful(sandbox: Sandbox):
    sandbox.notebook.exec_cell("test_stateful = 1")

    result = sandbox.notebook.exec_cell("test_stateful+=1; test_stateful")
    assert result.text == "2"
