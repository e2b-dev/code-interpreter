from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_reconnect(sandbox: CodeInterpreter):
    sandbox_id = sandbox.sandbox_id

    sandbox2 = CodeInterpreter.connect(sandbox_id)
    result = sandbox2.notebook.exec_cell("x =1; x")
    assert result.text == "1"
