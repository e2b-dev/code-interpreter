from e2b_code_interpreter.main import CodeInterpreter


def test_bash():
    with CodeInterpreter() as sandbox:
        result = sandbox.notebook.exec_cell("echo 'E2B is awesome!'")
        print(result.execution_count)
        result = sandbox.notebook.exec_cell("!pwd")
        print(result.execution_count)
        result = sandbox.notebook.exec_cell("!pwd")
        print(result.execution_count)

