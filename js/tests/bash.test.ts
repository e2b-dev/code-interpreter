import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('bash', async () => {
  const sandbox = await CodeInterpreter.create()

  const result = await sandbox.notebook.execCell('!pwd')

  expect(result.logs.stdout.join().trim()).toEqual('/home/user')

  await sandbox.close()
})
