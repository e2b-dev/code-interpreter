import { expect } from 'vitest'

import { isDebug, sandboxTest } from './setup'

sandboxTest('create context with no options', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  expect(context.id).toBeDefined()
  expect(context.language).toBe('python')
  expect(context.cwd).toBe('/home/user')
})

sandboxTest('create context with options', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext({
    language: 'python',
    cwd: '/home/user/test',
  })

  expect(context.id).toBeDefined()
  expect(context.language).toBe('python')
  expect(context.cwd).toBe('/home/user/test')
})

sandboxTest('remove context', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  await sandbox.removeCodeContext(context.id)
})

sandboxTest('list contexts', async ({ sandbox }) => {
  const contexts = await sandbox.listCodeContexts()

  expect(contexts.length).toBeGreaterThan(0)
})

sandboxTest('restart context', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  await sandbox.restartCodeContext(context.id)
})
