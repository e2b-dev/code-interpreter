import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('create context with no options', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  // wait 1 second for the context to be created
  await new Promise((resolve) => setTimeout(resolve, 1000))

  const contexts = await sandbox.listCodeContexts()
  const lastContext = contexts[contexts.length - 1]

  expect(lastContext.id).toBeDefined()
  expect(lastContext.language).toBe(context.language)
  expect(lastContext.cwd).toBe(context.cwd)
})

sandboxTest('create context with options', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext({
    language: 'python',
    cwd: '/root',
  })

  // wait 1 second for the context to be created
  await new Promise((resolve) => setTimeout(resolve, 1000))

  const contexts = await sandbox.listCodeContexts()
  const lastContext = contexts[contexts.length - 1]

  expect(lastContext.id).toBeDefined()
  expect(lastContext.language).toBe(context.language)
  expect(lastContext.cwd).toBe(context.cwd)
})

sandboxTest('remove context', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  await sandbox.removeCodeContext(context.id)
  const contexts = await sandbox.listCodeContexts()

  expect(contexts.map((context) => context.id)).not.toContain(context.id)
})

sandboxTest('list contexts', async ({ sandbox }) => {
  const contexts = await sandbox.listCodeContexts()

  // default contexts should include python and javascript
  expect(contexts.map((context) => context.language)).toContain('python')
  expect(contexts.map((context) => context.language)).toContain('javascript')
})

sandboxTest('restart context', async ({ sandbox }) => {
  const context = await sandbox.createCodeContext()

  // set a variable in the context
  await sandbox.runCode('x = 1', { context: context })

  // restart the context
  await sandbox.restartCodeContext(context.id)

  // check that the variable no longer exists
  const execution = await sandbox.runCode('x', { context: context })

  // check for an NameError with message "name 'x' is not defined"
  expect(execution.error).toBeDefined()
  expect(execution.error?.name).toBe('NameError')
  expect(execution.error?.value).toBe("name 'x' is not defined")
})
