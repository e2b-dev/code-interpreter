import { expect } from 'vitest'

import { Sandbox } from '../src'
import { sandboxTest } from './setup'

sandboxTest('reconnect', async ({ sandbox }) => {
  sandbox = await Sandbox.connect(sandbox.sandboxId)

  const result = await sandbox.runCode('x =1; x')

  expect(result.text).toEqual('1')
})
