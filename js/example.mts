import dotenv from 'dotenv'

import { Sandbox } from './dist'

dotenv.config()

const code = `
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()

x = np.linspace(0, 10, 100)
plt.plot(x, y)
plt.show()

import pandas
pandas.DataFrame({"a": [1, 2, 3]})
`

const sandbox = await Sandbox.create()
console.log(sandbox.sandboxId)

const execution = await sandbox.runCode(code, {
  onStdout(msg) {
    console.log('stdout', msg)
  },
  onStderr(msg) {
    console.log('stderr', msg)
  },
})
console.log(execution.results[0].formats())
console.log(execution.results[0].data)
console.log(execution.results.length)
