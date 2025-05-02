import pytest

from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_js_kernel(sandbox: Sandbox):
    execution = sandbox.run_code("console.log('Hello, World!')", language="js")
    assert execution.logs.stdout == ["Hello, World!\n"]


@pytest.mark.skip_debug()
def test_r_kernel(sandbox: Sandbox):
    execution = sandbox.run_code('print("Hello, World!")', language="r")
    assert execution.logs.stdout == ['[1] "Hello, World!"\n']


@pytest.mark.skip_debug()
def test_java_kernel(sandbox: Sandbox):
    execution = sandbox.run_code('System.out.println("Hello, World!")', language="java")
    assert execution.logs.stdout[0] == "Hello, World!"
