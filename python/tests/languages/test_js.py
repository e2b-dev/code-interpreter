from e2b_code_interpreter import AsyncSandbox


async def test_javascript(async_sandbox: AsyncSandbox):
    code = """
    console.log('Hello, World!')
    """
    execution = await async_sandbox.run_code(code, language="js")
    assert execution.logs.stdout == ["Hello, World!\n"]


async def test_import(async_sandbox: AsyncSandbox):
    code = """
    import isOdd from 'npm:is-odd'
    isOdd(3)
    """
    execution = await async_sandbox.run_code(code, language="js")
    assert execution.results[0].text == "true"


async def test_toplevel_await(async_sandbox: AsyncSandbox):
    code = """
    async function main() {
        return 'Hello, World!'
    }
    
    await main()
    """
    execution = await async_sandbox.run_code(code, language="js")
    assert execution.results[0].text == "Hello, World!"


async def test_es6(async_sandbox: AsyncSandbox):
    code = """
const add = (x, y) => x + y;
add(1, 2);
    """
    execution = await async_sandbox.run_code(code, language="js")
    assert execution.results[0].text == "3"


async def test_context(async_sandbox: AsyncSandbox):
    await async_sandbox.run_code("const x = 1", language="js")
    execution = await async_sandbox.run_code("x", language="js")
    assert execution.results[0].text == "1"


async def test_cwd(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code("process.cwd()", language="js")
    assert execution.results[0].text == "/home/user"

    ctx = await async_sandbox.create_code_context("/home", language="js")
    execution = await async_sandbox.run_code("process.cwd()", context=ctx)
    assert execution.results[0].text == "/home"


async def test_typescript(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        """
function subtract(x: number, y: number): number {
  return x - y;
}
  
subtract(1, 2);
""",
        language="ts",
    )
    assert execution.results[0].text == "-1"
