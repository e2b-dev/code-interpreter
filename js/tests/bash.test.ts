import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('bash', async () => {
  const sandbox = await CodeInterpreter.create()

  const output = await sandbox.notebook.execCell('!pwd')

  expect(output.stdout.join().trim()).toEqual('/home/user')

  await sandbox.close()
})
