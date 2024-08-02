import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('basic', async ({ sandbox }) => {
  const result = await sandbox.notebook.execCell('x =1; x')

  expect(result.text).toEqual('1')
})
