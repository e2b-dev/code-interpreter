import dotenv from 'dotenv'

import { CodeInterpreter } from './dist'

dotenv.config()

console.log('api', process.env.E2B_API_KEY)
console.log('api', process.env.E2B_DOMAIN)


const start = Date.now()

const sandbox = await CodeInterpreter.create()
console.log(`Time taken: ${Date.now() - start}ms`)
const r = await sandbox.notebook.execCell('x = 1; x')
console.log(r)
