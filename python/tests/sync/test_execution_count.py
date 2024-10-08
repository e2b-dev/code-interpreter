import pytest

from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


@pytest.mark.skip_debug()
def test_execution_count(sandbox: CodeInterpreter):
    sandbox.notebook.exec_cell("echo 'E2B is awesome!'")
    result = sandbox.notebook.exec_cell("!pwd")
    assert result.execution_count == 2
