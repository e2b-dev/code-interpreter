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


@pytest.mark.skip_debug()
def test_ts_kernel(sandbox: Sandbox):
    execution = sandbox.run_code("const message: string = 'Hello, World!'; console.log(message)", language="ts")
    assert execution.logs.stdout == ["Hello, World!\n"]


def test_ts_kernel_errors(sandbox: Sandbox):
    execution = sandbox.run_code("import x from 'module';", language="ts")
    assert execution.error is not None
    assert execution.error.name == "TypeScriptCompilerError"
