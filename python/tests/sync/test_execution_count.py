import pytest

from e2b_code_interpreter.code_interpreter_sync import Sandbox


@pytest.mark.skip_debug()
def test_execution_count(sandbox: Sandbox):
    sandbox.notebook.exec_cell("echo 'E2B is awesome!'")
    result = sandbox.notebook.exec_cell("!pwd")
    assert result.execution_count == 2
