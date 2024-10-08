import { expect } from 'vitest'

import { isDebug, sandboxTest } from './setup'

// Skip this test if we are running in debug mode — we don't create new sandbox for each test so the execution number is not reset.
sandboxTest.skipIf(isDebug)('execution count', async ({ sandbox }) => {
  await sandbox.notebook.execCell('!pwd')
  const result = await sandbox.notebook.execCell('!pwd')

  expect(result.executionCount).toEqual(2)
})
