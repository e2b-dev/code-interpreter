from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_create_context_with_no_options(sandbox: Sandbox):
    context = sandbox.create_code_context()

    assert context.id is not None
    assert context.language == "python"
    assert context.cwd == "/home/user"


def test_create_context_with_options(sandbox: Sandbox):
    context = sandbox.create_code_context(
        language="python",
        cwd="/home/user/test",
    )

    assert context.id is not None
    assert context.language == "python"
    assert context.cwd == "/home/user/test"


def test_remove_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    sandbox.remove_code_context(context.id)


def test_list_contexts(sandbox: Sandbox):
    contexts = sandbox.list_code_contexts()

    assert len(contexts) > 0


def test_restart_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    sandbox.restart_code_context(context.id)

