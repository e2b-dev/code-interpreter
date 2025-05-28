import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('test js kernel', async ({ sandbox }) => {
  const output = await sandbox.runCode('console.log("Hello World!")', {
    language: 'js',
  })
  expect(output.logs.stdout).toEqual(['Hello World!\n'])
})

sandboxTest('test ts kernel', async ({ sandbox }) => {
  const output = await sandbox.runCode(
    'const message: string = "Hello World!"; console.log(message)',
    { language: 'ts' }
  )
  expect(output.logs.stdout).toEqual(['Hello World!\n'])
})
