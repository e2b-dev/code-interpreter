import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('get data', async ({ sandbox }) => {
  const execution = await sandbox.notebook.execCell('pd.DataFrame({"a": [1, 2, 3]})')

  const result = execution.results[0]
  expect(result.data).toBeDefined()
})
