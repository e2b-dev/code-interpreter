import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('js simple', async ({ sandbox }) => {
  const result = await sandbox.runCode('console.log("Hello, World!")', {language: "js"})

  expect(result.logs.stdout.join().trim()).toEqual('Hello, World!')
})

sandboxTest('js import', async ({ sandbox }) => {
  const result = await sandbox.runCode('import isOdd from "npm:is-odd"\nisOdd(3)', {language: "js"})

  expect(result.results[0].text).toEqual('true')
})

sandboxTest('js top level await', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
    async function main() {
        return 'Hello, World!'
    }

    await main()
    `, {language: "js"})
  expect(result.results[0].text).toEqual('Hello, World!')
})

sandboxTest('js es6', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
const add = (x, y) => x + y;
add(1, 2)
`, {language: "js"})
  expect(result.results[0].text).toEqual('3')
})


sandboxTest('js context', async ({ sandbox }) => {
  await sandbox.runCode('const z = 1', {language: "js"})
  const result = await sandbox.runCode('z', {language: "js"})
  expect(result.results[0].text).toEqual('1')
})

sandboxTest('js cwd', async ({ sandbox }) => {
  const result = await sandbox.runCode('process.cwd()', {language: "js"})
  expect(result.results[0].text).toEqual('/home/user')

  const ctx = await sandbox.createCodeContext( {cwd: '/home', language: "js"})
  const result2 = await sandbox.runCode('process.cwd()', {context: ctx})
  expect(result2.results[0].text).toEqual('/home')
})

sandboxTest('ts simple', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
function subtract(x: number, y: number): number {
  return x - y;
}

subtract(1, 2)
`, {language: "ts"})

  expect(result.results[0].text).toEqual('-1')
})
