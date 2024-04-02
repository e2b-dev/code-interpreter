import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('statefulness', async () => {
  const sandbox = await CodeInterpreter.create()

  await sandbox.notebook.execCell('x = 1')

  const result = await sandbox.notebook.execCell('x += 1; x')

  expect(result.text).toEqual('2')

  await sandbox.close()
})
