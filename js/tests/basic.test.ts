import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('basic', async () => {
  const sandbox = await CodeInterpreter.create()

  const output = await sandbox.notebook.execCell('x =1; x')

  expect(output.result['text/plain']).toEqual('1')

  await sandbox.close()
})
