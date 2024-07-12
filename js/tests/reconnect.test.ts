import { expect } from 'vitest'

import { CodeInterpreter } from '../src'
import { sandboxTest } from './setup'

sandboxTest('reconnect', async ({ sandbox }) => {
  sandbox = await CodeInterpreter.connect(sandbox.sandboxID)

  const result = await sandbox.notebook.execCell('x =1; x')

  expect(result.text).toEqual('1')
})
