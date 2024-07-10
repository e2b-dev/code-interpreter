from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_bash():
    with CodeInterpreter() as sandbox:
        result = sandbox.notebook.exec_cell("!pwd")
        assert "".join(result.logs.stdout).strip() == "/home/user"
