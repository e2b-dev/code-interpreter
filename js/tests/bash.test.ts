import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('bash', async ({ sandbox }) => {
  const result = await sandbox.notebook.execCell('!pwd')

  expect(result.logs.stdout.join().trim()).toEqual('/home/user')
})
