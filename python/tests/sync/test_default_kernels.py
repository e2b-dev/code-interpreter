from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_js_kernel(sandbox: Sandbox):
    execution = sandbox.run_code("console.log('Hello, World!')", language="js")
    assert execution.logs.stdout == ["Hello, World!\n"]
