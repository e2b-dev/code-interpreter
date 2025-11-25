from e2b_code_interpreter.code_interpreter_sync import Sandbox
import time


def test_create_context_with_no_options(sandbox: Sandbox):
    context = sandbox.create_code_context()

    # wait 1 second for the context to be created
    time.sleep(1)

    contexts = sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


def test_create_context_with_options(sandbox: Sandbox):
    context = sandbox.create_code_context(
        language="python",
        cwd="/root",
    )

    # wait 1 second for the context to be created
    time.sleep(1)

    contexts = sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


def test_remove_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    sandbox.remove_code_context(context.id)

    contexts = sandbox.list_code_contexts()
    assert context.id not in [ctx.id for ctx in contexts]


def test_list_contexts(sandbox: Sandbox):
    contexts = sandbox.list_code_contexts()

    # default contexts should include python and javascript
    languages = [context.language for context in contexts]
    assert "python" in languages
    assert "javascript" in languages


def test_restart_context(sandbox: Sandbox):
    context = sandbox.create_code_context()

    # set a variable in the context
    sandbox.run_code("x = 1", context=context)

    # restart the context
    sandbox.restart_code_context(context.id)

    # check that the variable no longer exists
    execution = sandbox.run_code("x", context=context)

    # check for a NameError with message "name 'x' is not defined"
    assert execution.error is not None
    assert execution.error.name == "NameError"
    assert execution.error.value == "name 'x' is not defined"
