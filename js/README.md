<p align="center">
  <img width="100" src="/readme-assets/logo-circle.png" alt="e2b logo">
</p>


<h1 align="center">
  Code interpreter extension for JavaScript
</h1>

<h4 align="center">
  <a href="https://pypi.org/project/e2b/">
    <img alt="Last 1 month downloads for the Python SDK" loading="lazy" width="200" height="20" decoding="async" data-nimg="1"
    style="color:transparent;width:auto;height:100%" src="https://img.shields.io/pypi/dm/e2b?label=PyPI%20Downloads">
  </a>
  <a href="https://www.npmjs.com/package/e2b">
    <img alt="Last 1 month downloads for the Python SDK" loading="lazy" width="200" height="20" decoding="async" data-nimg="1"
    style="color:transparent;width:auto;height:100%" src="https://img.shields.io/npm/dm/e2b?label=NPM%20Downloads">
  </a>
</h4>


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
await sbx.runCode()('x = 1')

const execution = await sbx.runCode()('x+=1; x')
console.log(execution.text)  // outputs 2

await sandbox.close()
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

### More resources
- Check out the [JavaScript/TypeScript](https://e2b.dev/docs/hello-world/js) and [Python](https://e2b.dev/docs/hello-world/py) "Hello World" guides to learn how to use our SDK.

- See [E2B documentation](https://e2b.dev/docs) to get started.

- Visit our [Cookbook](https://github.com/e2b-dev/e2b-cookbook/tree/main) to get inspired by examples with different LLMs and AI frameworks.


___

<div align='center'>
<!-- <a href="https://e2b.dev/docs" target="_blank">
<img src="https://img.shields.io/badge/docs-%2300acee.svg?color=143D52&style=for-the-badge&logo=x&logoColor=white" alt=docs style="margin-bottom: 5px;"/></a>  -->
<a href="https://twitter.com/e2b_dev" target="_blank">
<img src="https://img.shields.io/badge/x (twitter)-%2300acee.svg?color=000000&style=for-the-badge&logo=x&logoColor=white" alt=linkedin style="margin-bottom: 5px;"/></a> 
<a href="https://discord.com/invite/U7KEcGErtQ" target="_blank">
<img src="https://img.shields.io/badge/discord -%2300acee.svg?color=143D52&style=for-the-badge&logo=discord&logoColor=white" alt=discord style="margin-bottom: 5px;"/></a> 
<a href="https://www.linkedin.com/company/e2b-dev/" target="_blank">
<img src="https://img.shields.io/badge/linkedin-%2300acee.svg?color=000000&style=for-the-badge&logo=linkedin&logoColor=white" alt=linkedin style="margin-bottom: 5px;"/></a> 
</div align='center'>