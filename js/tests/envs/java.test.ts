import { expect } from 'vitest'

import { isDebug, sandboxTest } from '../setup'
import { Sandbox } from '../../src'

// Java Env Vars
sandboxTest.skipIf(isDebug)('env vars on sandbox (java)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `System.out.println(System.getenv("TEST_ENV_VAR"))`,
      {
        language: 'java',
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars per execution (java)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    `System.out.println(System.getenv("FOO"))`,
    {
      envs: { FOO: 'bar' },
      language: 'java',
    }
  )

  const result_empty = await sandbox.runCode(
    `System.out.println(System.getenv("FOO") != null ? System.getenv("FOO") : "default")`,
    {
      language: 'java',
    }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
  expect(result_empty.results[0]?.text.trim()).toEqual('default')
})

sandboxTest.skipIf(isDebug)('env vars overwrite', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `System.out.println(System.getenv("TEST_ENV_VAR"))`,
      {
        language: 'java',
        envs: { TEST_ENV_VAR: 'overwrite' },
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('overwrite')
  } finally {
    await sandbox.kill()
  }
})
