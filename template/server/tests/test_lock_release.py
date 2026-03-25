"""
Regression test for issue #213: asyncio.Lock not released on client disconnect.

The lock in ContextWebSocket.execute() must only be held while sending the
request to the Jupyter kernel, NOT during the entire streaming phase. Holding
it during streaming means a client disconnect leaves the lock held until the
kernel finishes — blocking all subsequent executions on the same context.

This test mocks the Jupyter WebSocket so no real kernel is needed.
"""

import asyncio
import sys
import os
import unittest
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from messaging import ContextWebSocket
from api.models.output import NumberOfExecutions


class TestLockRelease(unittest.IsolatedAsyncioTestCase):
    async def test_lock_not_held_during_streaming(self):
        """Lock must be released before streaming results, not after."""
        ws = ContextWebSocket("test-ctx", "test-session", "python", "/home/user")

        # Mock the WebSocket so we don't need a real Jupyter kernel.
        ws._ws = AsyncMock()
        ws._ws.send = AsyncMock()

        # Pre-set global env vars so execute() doesn't call get_envs().
        ws._global_env_vars = {}

        # Start the execute() generator.
        gen = ws.execute("print('hello')", env_vars={}, access_token="")

        # Drive the generator: it acquires the lock, sends the request, then
        # enters _wait_for_result which blocks on queue.get(). We feed an item
        # into the queue so the generator yields it back to us.
        async def pull_first_item():
            return await gen.__anext__()

        pull_task = asyncio.create_task(pull_first_item())

        # Wait for the generator to register the execution and send the request.
        await asyncio.sleep(0.1)

        # Feed an item into the execution queue so _wait_for_result yields.
        assert len(ws._executions) == 1
        message_id = list(ws._executions.keys())[0]
        await ws._executions[message_id].queue.put(
            NumberOfExecutions(execution_count=1)
        )

        # Get the yielded item — generator is now suspended at the next
        # queue.get() inside _wait_for_result (the streaming phase).
        await asyncio.wait_for(pull_task, timeout=2.0)

        # THE KEY ASSERTION: the lock must NOT be held during streaming.
        # Without fix: lock is held for entire execute() -> locked() is True -> FAIL
        # With fix: lock released after send -> locked() is False -> PASS
        assert not ws._lock.locked(), (
            "Lock is held during result streaming — issue #213: if the client "
            "disconnects now, the lock stays held and blocks all subsequent "
            "executions on this context"
        )

        # Cleanup: close the generator properly.
        await gen.aclose()


if __name__ == "__main__":
    unittest.main()
