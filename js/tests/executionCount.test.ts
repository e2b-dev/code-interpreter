import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('execution count', async () => {
  const sandbox = await CodeInterpreter.create()

  await sandbox.notebook.execCell('!pwd')
  const result = await sandbox.notebook.execCell('!pwd')


  await sandbox.close()

  expect(result.executionCount).toEqual(2)
})
