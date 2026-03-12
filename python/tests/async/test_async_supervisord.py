import asyncio

from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


async def wait_for_health(sandbox: AsyncSandbox, max_retries=10, interval_ms=100):
    for _ in range(max_retries):
        result = await sandbox.commands.run(
            'curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:49999/health'
        )
        if result.stdout.strip() == "200":
            return True
        await asyncio.sleep(interval_ms / 1000)
    return False


async def test_restart_after_jupyter_kill(async_sandbox: AsyncSandbox):
    # Verify health is up initially
    assert await wait_for_health(async_sandbox)

    # Kill the jupyter process
    await async_sandbox.commands.run("supervisorctl stop jupyter")

    # Wait for supervisord to restart it and health to come back
    assert await wait_for_health(async_sandbox, 10, 100)

    # Verify code execution works after recovery
    result = await async_sandbox.run_code("x = 1; x")
    assert result.text == "1"


async def test_restart_after_code_interpreter_kill(async_sandbox: AsyncSandbox):
    # Verify health is up initially
    assert await wait_for_health(async_sandbox)

    # Kill the code-interpreter process
    await async_sandbox.commands.run("supervisorctl stop code-interpreter")

    # Wait for supervisord to restart it and health to come back
    assert await wait_for_health(async_sandbox, 10, 100)

    # Verify code execution works after recovery
    result = await async_sandbox.run_code("x = 1; x")
    assert result.text == "1"
