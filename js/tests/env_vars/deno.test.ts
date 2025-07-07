import { expect } from 'vitest'

import { isDebug, sandboxTest } from '../setup'
import { Sandbox } from '../../src'

// Deno Env Vars
sandboxTest.skipIf(isDebug)('env vars on sandbox (deno)', async ({ template }) => {
  const sandbox = await Sandbox.create(template, {
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `Deno.env.get('TEST_ENV_VAR')`,
      {
        language: 'deno',
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars per execution (deno)', async ({ sandbox }) => {
  const result = await sandbox.runCode("Deno.env.get('FOO')", {
    envs: { FOO: 'bar' },
    language: 'deno',
  })

  const result_empty = await sandbox.runCode(
    "Deno.env.get('FOO') ?? 'default'",
    {
      language: 'deno',
    }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
  expect(result_empty.results[0]?.text.trim()).toEqual('default')
})

sandboxTest.skipIf(isDebug)('env vars overwrite', async ({ template }) => {
  const sandbox = await Sandbox.create(template, {
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `Deno.env.get('TEST_ENV_VAR')`,
      {
        language: 'deno',
        envs: { TEST_ENV_VAR: 'overwrite' },
      }
    )

    const result_global_default = await sandbox.runCode(
      `Deno.env.get('TEST_ENV_VAR')`,
      {
        language: 'deno',
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('overwrite')
    expect(result_global_default.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})
