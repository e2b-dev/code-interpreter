from e2b import TimeoutException
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox

import pytest


async def test_execution_after_timeout_is_not_blocked(async_sandbox: AsyncSandbox):
    """After a client-side timeout, subsequent executions should not be blocked
    behind an orphaned lock. Regression test for issue #213.

    Uses its own context to avoid blocking other parallel tests with the sleep.
    """

    context = await async_sandbox.create_code_context()

    # sleep(5) with 2s timeout: client disconnects at 2s, kernel finishes at 5s.
    with pytest.raises(TimeoutException):
        await async_sandbox.run_code(
            "import time; time.sleep(5)", context=context, timeout=2
        )

    # With the fix (lock released after send), this sends immediately and
    # succeeds once the kernel finishes the sleep. Without the fix, this
    # blocks on the server lock indefinitely.
    result = await async_sandbox.run_code("x = 1; x", context=context, timeout=15)
    assert result.text == "1"
