import dotenv from 'dotenv'

import { CodeInterpreter } from './dist'

dotenv.config()

const code = `
pd.DataFrame({"a": [1, 2, 3]})
`

const sandbox = await CodeInterpreter.create("ci-df")
console.log(sandbox.sandboxId)

const execution = await sandbox.notebook.execCell(code, {
})
console.log(execution.results[0].formats())
console.log(execution.results[0].data)
console.log(execution.results.length)
