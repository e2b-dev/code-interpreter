const { CodeInterpreter } = require('./dist')
const dotenv = require('dotenv')
dotenv.config();

async function main() {
    const sandbox = await CodeInterpreter.create()
    const r =await sandbox.notebook.execCell('x = 1; x')
    console.log(r)
}

main().catch(console.error)

