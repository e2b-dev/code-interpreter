from e2b_code_interpreter.main import CodeInterpreter


def test_basic():
    with CodeInterpreter() as sandbox:
        result = sandbox.notebook.exec_cell("x =1; x")
        assert result.output == "1"
