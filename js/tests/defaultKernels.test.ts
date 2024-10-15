import { expect } from 'vitest'

import { sandboxTest } from './setup'

sandboxTest('test js kernel', async ({ sandbox }) => {
  const output = await sandbox.runCode('console.log("Hello World!")', { language: 'js' })
  console.log(output)
  expect(output.logs.stdout).toEqual(['Hello World!\n'])
})
