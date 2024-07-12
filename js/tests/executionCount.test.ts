import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('execution count', async ({ sandbox }) => {
  await sandbox.notebook.execCell('!pwd')
  const result = await sandbox.notebook.execCell('!pwd')

  expect(result.executionCount).toEqual(2)
})
