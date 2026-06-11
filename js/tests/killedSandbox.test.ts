import { TimeoutError } from 'e2b'
import { expect } from 'vitest'

import { isDebug, sandboxTest, wait } from './setup'

sandboxTest.skipIf(isDebug)(
  'runCode throws a descriptive error when the sandbox is killed during execution',
  async ({ sandbox }) => {
    const execution = sandbox.runCode('import time; time.sleep(60)')
    const assertion = Promise.all([
      expect(execution).rejects.toThrowError(
        /sandbox was killed while the request was in progress/
      ),
      expect(execution).rejects.toBeInstanceOf(TimeoutError),
    ])

    await wait(2_000)
    await sandbox.kill()

    await assertion
  }
)
