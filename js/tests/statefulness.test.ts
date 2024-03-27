import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('statefulness', async () => {
  const sandbox = await CodeInterpreter.create()

  await sandbox.notebook.execCell('x = 1')

  const output = await sandbox.notebook.execCell('x += 1; x')

  expect(output.result['text/plain']).toEqual('2')

  await sandbox.close()
})
