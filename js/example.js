const { CodeInterpreter } = require('./dist')
const dotenv = require('dotenv')
dotenv.config()

async function main() {
const sandbox = await CodeInterpreter.create()
const jsID = await sandbox.notebook.createKernel({kernelName: "javascript"})
const execution = await sandbox.notebook.execCell("console.log('Hello World!')", { kernelID: jsID })
console.log(execution)

}

main().catch(console.error)
