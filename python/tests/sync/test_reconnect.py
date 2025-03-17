from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_reconnect(sandbox: Sandbox):
    sandbox_id = sandbox.sandbox_id

    sandbox2 = Sandbox.connect(sandbox_id, auto_pause=True)
    result = sandbox2.run_code("x =1; x")
    assert result.text == "1"
