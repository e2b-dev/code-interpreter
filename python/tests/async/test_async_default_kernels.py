from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def test_js_kernel(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        "console.log('Hello, World!')", language="js"
    )
    assert execution.logs.stdout == ["Hello, World!\n"]


async def test_ts_kernel(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        "const message: string = 'Hello, World!'; console.log(message);", language="ts"
    )
    assert execution.logs.stdout == ["Hello, World!\n"]


async def test_ts_kernel_errors(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        "import x from 'module';", language="ts"
    )
    assert execution.error is not None
    assert execution.error.name == "TypeScriptCompilerError"


async def test_ruby_kernel(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code("puts 'Hello, World!'", language="ruby")
    assert execution.logs.stdout == ["Hello, World!\n"]
