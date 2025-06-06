import { expect } from 'vitest'

import { isDebug, sandboxTest } from '../setup'
import { Sandbox } from '../../src'

// Bash Env Vars
sandboxTest.skipIf(isDebug)('env vars on sandbox (bash)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `echo $TEST_ENV_VAR`,
      {
        language: 'bash',
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars per execution (bash)', async ({ sandbox }) => {
  const result = await sandbox.runCode('echo $FOO', {
    envs: { FOO: 'bar' },
    language: 'bash',
  })

  const result_empty = await sandbox.runCode(
    'echo ${FOO:-default}',
    {
      language: 'bash',
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
      `echo $TEST_ENV_VAR`,
      {
        language: 'bash',
        envs: { TEST_ENV_VAR: 'overwrite' },
      }
    )

    expect(result.results[0]?.text.trim()).toEqual('overwrite')
  } finally {
    await sandbox.kill()
  }
})
