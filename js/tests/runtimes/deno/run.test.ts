import { assertEquals } from 'https://deno.land/std@0.224.0/assert/mod.ts'
import { load } from 'https://deno.land/std@0.224.0/dotenv/mod.ts'

await load({ envPath: '.env', export: true })

import { CodeInterpreter } from '../../../dist/index.mjs'


Deno.test('Deno test', async () => {
  const sbx = await CodeInterpreter.create({ timeoutMs: 5_000 })
  try {
    const result = await sbx.notebook.execCell('print("Hello, World!")')
    assertEquals(result.logs.stdout.join(''), 'Hello, World!\n')
  } finally {
    await sbx.kill()
  }
})
