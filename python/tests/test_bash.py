from e2b_code_interpreter.main import CodeInterpreter


def test_bash():
    with CodeInterpreter() as sandbox:
        result = sandbox.notebook.exec_cell("!pwd")
        assert "".join(result.logs.stdout).strip() == "/home/user"
