import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('basic', async () => {
  const sandbox = await CodeInterpreter.create()

  const result = await sandbox.notebook.execCell('x =1; x')

  expect(result.text).toEqual('1')

  await sandbox.close()
})
