const { CodeInterpreter } = require('../dist')
const dotenv = require('dotenv')
dotenv.config()

const iterations = 10
let createSandboxTime = 0
let fistExecTime = 0
let secondExecTime = 0

async function main() {
  for (let i = 0; i < iterations; i++) {
    console.log('Iteration:', i + 1)
    let startTime = new Date()
    const sandbox = await CodeInterpreter.create()
    createSandboxTime += new Date() - startTime

    startTime = new Date()
    await sandbox.notebook.execCell('x = 1')
    fistExecTime += new Date() - startTime

    startTime = new Date()
    const result = await sandbox.notebook.execCell('x+=1; x')
    secondExecTime += new Date() - startTime

    await sandbox.close()
  }
  console.log('Average create sandbox time:', createSandboxTime / iterations)
  console.log('Average first exec time:', fistExecTime / iterations)
  console.log('Average second exec time:', secondExecTime / iterations)
}
main().catch(console.error)
