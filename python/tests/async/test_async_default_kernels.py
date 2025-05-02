from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_js_kernel(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        "console.log('Hello, World!')", language="js"
    )
    assert execution.logs.stdout == ["Hello, World!\n"]
