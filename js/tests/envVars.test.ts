import { expect } from 'vitest'

import { isDebug, sandboxTest } from './setup'
import { Sandbox } from '../src'

// Python tests
sandboxTest.skipIf(isDebug)('env vars (python)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `import os; x = os.getenv('TEST_ENV_VAR'); x`
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox (python)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    "import os; os.getenv('FOO')",
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
})

// JavaScript tests
sandboxTest.skipIf(isDebug)('env vars (javascript)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `process.env.TEST_ENV_VAR`
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox (javascript)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    `process.env.FOO`,
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
})

// R tests
sandboxTest.skipIf(isDebug)('env vars (r)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `Sys.getenv("TEST_ENV_VAR")`
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox (r)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    `Sys.getenv("FOO")`,
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
})

// Java tests
sandboxTest.skipIf(isDebug)('env vars (java)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `System.getenv("TEST_ENV_VAR")`
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox (java)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    `System.getenv("FOO")`,
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
})

// Bash tests
sandboxTest.skipIf(isDebug)('env vars (bash)', async () => {
  const sandbox = await Sandbox.create({
    envs: { TEST_ENV_VAR: 'supertest' },
  })

  try {
    const result = await sandbox.runCode(
      `echo $TEST_ENV_VAR`
    )

    expect(result.results[0]?.text.trim()).toEqual('supertest')
  } finally {
    await sandbox.kill()
  }
})

sandboxTest('env vars on sandbox (bash)', async ({ sandbox }) => {
  const result = await sandbox.runCode(
    `echo $FOO`,
    { envs: { FOO: 'bar' } }
  )

  expect(result.results[0]?.text.trim()).toEqual('bar')
})
