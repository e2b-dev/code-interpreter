from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_execution_count():
    with CodeInterpreter() as sandbox:
        sandbox.notebook.exec_cell("echo 'E2B is awesome!'")
        result = sandbox.notebook.exec_cell("!pwd")
        assert result.execution_count == 2
