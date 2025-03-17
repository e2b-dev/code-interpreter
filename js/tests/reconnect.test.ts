import { expect } from 'vitest'

import { Sandbox } from '../src'
import { sandboxTest, timeoutMs } from './setup'

sandboxTest('reconnect', async ({ sandbox }) => {
  sandbox = await Sandbox.connect(sandbox.sandboxId, { timeoutMs, autoPause: true })

  const result = await sandbox.runCode('x =1; x')

  expect(result.text).toEqual('1')
})
