from e2b_code_interpreter.code_interpreter_sync import Sandbox


def test_create_context_with_no_options(sandbox: Sandbox):
    context = sandbox.create_code_context()

    contexts = sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


def test_create_context_with_options(sandbox: Sandbox):
    context = sandbox.create_code_context(
        language="python",
        cwd="/home/user/test",
    )

    contexts = sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


def test_remove_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    sandbox.remove_code_context(context.id)


def test_list_contexts(sandbox: Sandbox):
    contexts = sandbox.list_code_contexts()

    # default contexts should include python and javascript
    languages = [context.language for context in contexts]
    assert "python" in languages
    assert "javascript" in languages


def test_restart_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    sandbox.restart_code_context(context.id)
