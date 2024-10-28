import { expect } from 'vitest'

import { isDebug, sandboxTest } from './setup'
import { Sandbox } from '../src'

// Skip this test if we are running in debug mode — the pwd and user in the testing docker container are not the same as in the actual sandbox.
sandboxTest.skipIf(isDebug)('env vars', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `import os; x = os.getenv('TEST_ENV_VAR'); x`
    )

    expect(result.results[0].text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    "import os; os.getenv('FOO')",
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0].text.trim()).toEqual('bar')
})

sandboxTest('env vars on sandbox override', async () => {
  const sandbox = await Sandbox.create({
    envs: { FOO: 'bar', SBX: 'value' },
  })

  try {
    await sandbox.runCode(
      "import os; os.environ['FOO'] = 'bar'; os.environ['RUNTIME_ENV'] = 'js_runtime'"
    )
    const result = await sandbox.runCode(
      "import os; os.getenv('FOO')",
      { envs: { FOO: 'baz' } }
    )

    expect(result.results[0].text.trim()).toEqual('baz')

    const result2 = await sandbox.runCode(
      "import os; os.getenv('RUNTIME_ENV')"
    )
    expect(result2.results[0].text.trim()).toEqual('js_runtime')

    if (!isDebug) {
      const result3 = await sandbox.runCode(
        "import os; os.getenv('SBX')"
      )
      expect(result3.results[0].text.trim()).toEqual('value')
    }

    const result4 = await sandbox.runCode("import os; os.getenv('FOO')")
    expect(result4.results[0].text.trim()).toEqual('bar')
  } finally {
    await sandbox.kill()
  }
})
