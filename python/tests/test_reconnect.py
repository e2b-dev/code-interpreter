from e2b_code_interpreter.main import CodeInterpreter


def test_reconnect():
    sandbox = CodeInterpreter()
    sandbox_id = sandbox.sandbox_id
    sandbox.close()

    sandbox2 = CodeInterpreter.connect(sandbox_id)
    result = sandbox2.notebook.exec_cell("x =1; x")
    sandbox2.close()
    assert result.text == "1"
