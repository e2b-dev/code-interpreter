# Code interpreter extension for JavaScript

The repository contains a template and modules for the code interpreter sandbox. It is based on the Jupyter server and implements the Jupyter Kernel messaging protocol. This allows for sharing context between code executions and improves support for plotting charts and other display-able data.

## Key Features

- **Stateful Execution**: Unlike traditional sandboxes that treat each code execution independently, this package maintains context across executions.
- **Displaying Charts & Data**: Implements parts of the [Jupyter Kernel messaging protocol](https://jupyter-client.readthedocs.io/en/latest/messaging.html), which support for interactive features like plotting charts, rendering DataFrames, etc.

## Installation

```sh
npm install @e2b/code-interpreter
```

## Examples

### Minimal example with the sharing context

```js
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
await sandbox.runCode('x = 1')

const execution = await sandbox.runCode('x+=1; x')
console.log(execution.text) // outputs 2

await sandbox.kill()
```

### Get charts and any display-able data

```js
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

const code = `
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()
`

// you can install dependencies in "jupyter notebook style"
await sandbox.runCode('!pip install matplotlib')

const execution = await sandbox.runCode(code)

// this contains the image data, you can e.g. save it to file or send to frontend
execution.results[0].png

await sandbox.kill()
```

### Streaming code output

```js
import { Sandbox } from '@e2b/code-interpreter'

const code = `
import time
import pandas as pd

print("hello")
time.sleep(3)
data = pd.DataFrame(data=[[1, 2], [3, 4]], columns=["A", "B"])
display(data.head(10))
time.sleep(3)
print("world")
`

const sandbox = await Sandbox.create()

await sandbox.runCode(code, {
  onStdout: (out) => console.log(out),
  onStderr: (outErr) => console.error(outErr),
  onResult: (result) => console.log(result.text),
})

await sandbox.kill()
```
