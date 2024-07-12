import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('statefulness', async ({ sandbox }) => {
  await sandbox.notebook.execCell('x = 1')

  const result = await sandbox.notebook.execCell('x += 1; x')

  expect(result.text).toEqual('2')
})
