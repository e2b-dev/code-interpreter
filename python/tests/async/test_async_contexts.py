from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_create_context_with_no_options(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    contexts = await async_sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


async def test_create_context_with_options(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context(
        language="python",
        cwd="/home/user/test",
    )

    contexts = await async_sandbox.list_code_contexts()
    last_context = contexts[-1]

    assert last_context.id is not None
    assert last_context.language == context.language
    assert last_context.cwd == context.cwd


async def test_remove_context(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    await async_sandbox.remove_code_context(context.id)


async def test_list_contexts(async_sandbox: AsyncSandbox):
    contexts = await async_sandbox.list_code_contexts()

    # default contexts should include python and javascript
    languages = [context.language for context in contexts]
    assert "python" in languages
    assert "javascript" in languages


async def test_restart_context(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    await async_sandbox.restart_code_context(context.id)
