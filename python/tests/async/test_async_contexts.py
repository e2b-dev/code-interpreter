from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_create_context_with_no_options(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    assert context.id is not None
    assert context.language == "python"
    assert context.cwd == "/home/user"


async def test_create_context_with_options(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context(
        language="python",
        cwd="/home/user/test",
    )

    assert context.id is not None
    assert context.language == "python"
    assert context.cwd == "/home/user/test"


async def test_remove_context(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    await async_sandbox.remove_code_context(context.id)


async def test_list_contexts(async_sandbox: AsyncSandbox):
    contexts = await async_sandbox.list_code_contexts()

    assert len(contexts) > 0


async def test_restart_context(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()

    await async_sandbox.restart_code_context(context.id)
