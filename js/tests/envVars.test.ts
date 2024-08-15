import { expect } from 'vitest'

import { sandboxTest } from './setup'
import { CodeInterpreter } from "../src";

// Skip this test if we are running in debug mode — the pwd and user in the testing docker container are not the same as in the actual sandbox.
sandboxTest('env vars', async () => {
  const sandbox = await CodeInterpreter.create('g0zptwsuemevq896f2u3', { envs: { TEST_ENV_VAR: "supertest" } })
  const result = await sandbox.notebook.execCell(`import os; x = os.getenv('TEST_ENV_VAR'); x`)

  expect(result.results[0].text.trim()).toEqual('supertest')
})

sandboxTest('env vars on sandbox', async ({sandbox}) => {
  const result = await sandbox.notebook.execCell("import os; os.getenv('FOO')", {envs: {FOO: "bar"}})

  expect(result.results[0].text.trim()).toEqual('bar')
})

sandboxTest('env vars on sandbox override', async () => {
  const sandbox = await CodeInterpreter.create('g0zptwsuemevq896f2u3', { envs: { FOO: "bar", SBX: "value" } })
  await sandbox.notebook.execCell("import os; os.environ['FOO'] = 'bar'); os.environ['RUNTIME_ENV'] = 'value'")
  const result = await sandbox.notebook.execCell("import os; os.getenv('FOO')", {envs: {FOO: "baz"}})

  expect(result.results[0].text.trim()).toEqual('baz')

  const result2 = await sandbox.notebook.execCell("import os; os.getenv('RUNTIME_ENV')")
  expect(result2.results[0].text.trim()).toEqual('value')

  const result3 = await sandbox.notebook.execCell("import os; os.getenv('SBX')")
  expect(result3.results[0].text.trim()).toEqual('value')

  const result4 = await sandbox.notebook.execCell("import os; os.getenv('FOO')")
  expect(result4.results[0].text.trim()).toEqual('bar')
})
