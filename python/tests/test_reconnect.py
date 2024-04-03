from e2b_code_interpreter.main import CodeInterpreter


def test_reconnect():
    with CodeInterpreter() as sandbox:
        sandbox_id = sandbox.id

    sandbox = CodeInterpreter.reconnect(sandbox_id)
    result = sandbox.notebook.exec_cell("x =1; x")
    assert result.text == "1"

    sandbox.close()
