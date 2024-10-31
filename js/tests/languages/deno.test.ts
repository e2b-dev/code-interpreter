import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('js simple', async ({ sandbox }) => {
  const result = await sandbox.runCode('console.log("Hello, World!")', {language: "deno"})

  expect(result.logs.stdout.join().trim()).toEqual('Hello, World!')
})

sandboxTest('js import', async ({ sandbox }) => {
  const result = await sandbox.runCode('import isOdd from "npm:is-odd"\nisOdd(3)', {language: "deno"})

  expect(result.results[0].text).toEqual('true')
})

sandboxTest('js top level await', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
    async function main() {
        return 'Hello, World!'
    }

    await main()
    `, {language: "deno"})
  expect(result.results[0].text).toEqual('Hello, World!')
})

sandboxTest('js es6', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
   const add = (x, y) => x + y;
   add(1, 2)`, {language: "deno"})
  expect(result.results[0].text).toEqual('3')
})


sandboxTest('js context', async ({ sandbox }) => {
  await sandbox.runCode('const z = 1', {language: "deno"})
  const result = await sandbox.runCode('z', {language: "deno"})
  expect(result.results[0].text).toEqual('1')
})

sandboxTest('js cwd', async ({ sandbox }) => {
  const result = await sandbox.runCode('process.cwd()', {language: "deno"})
  expect(result.results[0].text).toEqual('/home/user')

  const ctx = await sandbox.createCodeContext( {cwd: '/home', language: "deno"})
  const result2 = await sandbox.runCode('process.cwd()', {context: ctx})
  expect(result2.results[0].text).toEqual('/home')
})

sandboxTest('ts simple', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
function subtract(x: number, y: number): number {
  return x - y;
}

subtract(1, 2)
`, {language: "deno"})

  expect(result.results[0].text).toEqual('-1')
})

sandboxTest('test display', async ({ sandbox }) => {
  const result = await sandbox.runCode(`
   {
  [Symbol.for("Jupyter.display")]() {
    return {
      // Plain text content
      "text/plain": "Hello world!",

      // HTML output
      "text/html": "<h1>Hello world!</h1>",
    }
  }
}
`, {language: "deno"})

  expect(result.results[0].html).toBe('<h1>Hello world!</h1>')
  expect(result.results[0].text).toBe('Hello world!')
})
