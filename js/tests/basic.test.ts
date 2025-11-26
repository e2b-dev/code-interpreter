import { expect } from 'vitest'
import { isDebug, sandboxTest } from './setup'
import { Sandbox } from '../src'

sandboxTest('basic', async ({ sandbox }) => {
  const result = await sandbox.runCode('x =1; x')

  expect(result.text).toEqual('1')
})

sandboxTest.skipIf(isDebug)('secure access', async ({ template }) => {
  const sandbox = await Sandbox.create(template, {
    network: {
      allowPublicTraffic: false,
    },
  })

  const result = await sandbox.runCode('x =1; x')

  expect(result.text).toEqual('1')

  await sandbox.kill()
})
