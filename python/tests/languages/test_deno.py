import pytest

from e2b_code_interpreter import AsyncSandbox


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_javascript(async_sandbox: AsyncSandbox):
    code = """
    console.log('Hello, World!')
    """
    execution = await async_sandbox.run_code(code, language="deno")
    assert execution.logs.stdout == ["Hello, World!\n"]


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_import(async_sandbox: AsyncSandbox):
    code = """
    import isOdd from 'npm:is-odd'
    isOdd(3)
    """
    execution = await async_sandbox.run_code(code, language="deno")
    assert execution.results[0].text == "true"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_toplevel_await(async_sandbox: AsyncSandbox):
    code = """
    async function main() {
        return 'Hello, World!'
    }
    
    await main()
    """
    execution = await async_sandbox.run_code(code, language="deno")
    assert execution.results[0].text == "Hello, World!"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_es6(async_sandbox: AsyncSandbox):
    code = """
const add = (x, y) => x + y;
add(1, 2);
    """
    execution = await async_sandbox.run_code(code, language="deno")
    assert execution.results[0].text == "3"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_context(async_sandbox: AsyncSandbox):
    await async_sandbox.run_code("const x = 1", language="deno")
    execution = await async_sandbox.run_code("x", language="deno")
    assert execution.results[0].text == "1"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_cwd(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code("process.cwd()", language="deno")
    assert execution.results[0].text == "/home/user"

    ctx = await async_sandbox.create_code_context("/home", language="deno")
    execution = await async_sandbox.run_code("process.cwd()", context=ctx)
    assert execution.results[0].text == "/home"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_typescript(async_sandbox: AsyncSandbox):
    execution = await async_sandbox.run_code(
        """
function subtract(x: number, y: number): number {
  return x - y;
}
  
subtract(1, 2);
""",
        language="deno",
    )
    assert execution.results[0].text == "-1"


@pytest.mark.skip(reason="Deno is not supported yet")
async def test_display(async_sandbox: AsyncSandbox):
    code = """
{
  [Symbol.for("Jupyter.display")]() {
    return {
      // Plain text content
      "text/plain": "Hello world!",

      // HTML output
      "text/html": "<h1>Hello world!</h1>",
    }
  }
}
    """
    execution = await async_sandbox.run_code(code, language="deno")
    assert execution.results[0].text == "Hello world!"
    assert execution.results[0].html == "<h1>Hello world!</h1>"
