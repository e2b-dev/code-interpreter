import dotenv from 'dotenv'

import { CodeInterpreter } from './dist'

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

const sandbox = await CodeInterpreter.connect("", { debug: true })
console.log(sandbox.sandboxID)

const execution = await sandbox.notebook.execCell(code, {
  onStdout(msg) {
    console.log('stdout', msg)
  },
  onStderr(msg) {
    console.log('stderr', msg)
  },
})
console.log(execution.results[0].formats())
console.log(execution.results.length)
