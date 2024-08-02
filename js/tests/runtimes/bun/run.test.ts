import { expect, test } from 'bun:test'

import { CodeInterpreter } from '../../../src'

test('Bun test', async () => {
  const sbx = await CodeInterpreter.create({ timeoutMs: 5_000 })
  try {
    const result = await sbx.notebook.execCell('print("Hello, World!")')
    expect(result.logs.stdout.join('')).toEqual('Hello, World!\n')
  } finally {
    await sbx.kill()
  }
})
