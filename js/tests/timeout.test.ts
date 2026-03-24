import { expect } from 'vitest'
import { sandboxTest } from './setup'

// Regression test for issue #213: asyncio.Lock not released on client disconnect.
// Uses its own context to avoid blocking other parallel tests with the sleep.
sandboxTest(
  'execution after timeout is not blocked',
  async ({ sandbox }) => {
    const context = await sandbox.createCodeContext()

    // sleep(5) with 2s timeout: client disconnects at 2s, kernel finishes at 5s.
    await expect(
      sandbox.runCode('import time; time.sleep(5)', {
        context,
        timeoutMs: 2_000,
      })
    ).rejects.toThrow()

    // With the fix (lock released after send), this sends immediately and
    // succeeds once the kernel finishes the sleep. Without the fix, this
    // blocks on the server lock indefinitely.
    const result = await sandbox.runCode('x = 1; x', {
      context,
      timeoutMs: 15_000,
    })
    expect(result.text).toEqual('1')
  },
)
