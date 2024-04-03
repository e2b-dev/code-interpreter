import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('reconnect', async () => {
  let sandbox = await CodeInterpreter.create()
  await sandbox.close()

  sandbox = await CodeInterpreter.reconnect(sandbox.id)

  const result = await sandbox.notebook.execCell('x =1; x')

  expect(result.text).toEqual('1')

  await sandbox.close()
})
