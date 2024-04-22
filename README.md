# Code Interpreter SDK
Built with [E2B](https://github.com/e2b-dev/e2b).


This Code Interpreter SDK allows you to run AI-generated Python code and each run share the context. That means that subsequent runs can reference to variables, definitions, etc from past code execution runs.
The code interpreter runs inside the [E2B Sandbox](https://github.com/e2b-dev/e2b) - an open-source secure micro VM made for running untrusted AI-generated code and AI agents.
- ✅ Works with any LLM and AI framework
- ✅ Supports streaming content like charts and stdout, stderr
- ✅ Python & JS SDK
- ✅ Runs on serverless and edge functions
- ✅ 100% open source (including [infrastructure](https://github.com/e2b-dev/infra))

Follow E2B on [X (Twitter)](https://twitter.com/e2b_dev)

<img width="1200" alt="Post-02" src="https://github.com/e2b-dev/code-interpreter/assets/5136688/2fa8c371-f03c-4186-b0b6-4151e68b0539">

## Getting started

### 🧑‍🍳 0. Cookbook
- [Claude with code intepreter](https://github.com/e2b-dev/e2b-cookbook/blob/main/examples/claude-code-interpreter/claude_code_interpreter.ipynb)
- 🦙 [Llama 3 with code interpreter](https://github.com/e2b-dev/e2b-cookbook/tree/main/examples/llama-3-code-interpreter)

### 1. Get your E2B API key
1. [Sign up](https://e2b.dev/docs/sign-in?view=sign-up)
2. [Get your API key](https://e2b.dev/docs/getting-started/api-key)

### 2. Install the SDK

**Python**

```sh
pip install e2b-code-interpreter
```

**JavaScript**

```sh
npm install @e2b/code-interpreter
```

### 3. Run the code interpreter

**Python**

```python
from e2b_code_interpreter import CodeInterpreter

with CodeInterpreter() as sandbox:
    sandbox.notebook.exec_cell("x = 1")

    execution = sandbox.notebook.exec_cell("x+=1; x")
    print(execution.text)  # outputs 2

```

**JavaScript**

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

const sandbox = await CodeInterpreter.create()
await sandbox.notebook.execCell('x = 1')

const execution = await sandbox.notebook.execCell('x+=1; x')
console.log(execution.text)  // outputs 2

await sandbox.close()
```

---

## How to customize the code interpreter sandbox

Follow [this guide](./template/README.md) if you want to customize the Code Interprerter sandbox (e.g.: add a preinstalled package). The customization is done via [custom E2B sandbox template](https://e2b.dev/docs/sandbox/templates/overview).

---

## Examples

### Minimal example with the sharing context

#### Python

```python
from e2b_code_interpreter import CodeInterpreter

with CodeInterpreter() as sandbox:
    sandbox.notebook.exec_cell("x = 1")

    execution = sandbox.notebook.exec_cell("x+=1; x")
    print(execution.text)  # outputs 2

```

#### JavaScript

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

const sandbox = await CodeInterpreter.create()
await sandbox.notebook.execCell('x = 1')

const execution = await sandbox.notebook.execCell('x+=1; x')
console.log(execution.text)  // outputs 2

await sandbox.close()
```

### Get charts and any display-able data

#### Python

```python
import base64
import io

from matplotlib import image as mpimg, pyplot as plt

from e2b_code_interpreter import CodeInterpreter

code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()
"""

with CodeInterpreter() as sandbox:
    # you can install dependencies in "jupyter notebook style"
    sandbox.notebook.exec_cell("!pip install matplotlib")

    # plot random graph
    execution = sandbox.notebook.exec_cell(code)

# there's your image
image = execution.results[0].png

# example how to show the image / prove it works
i = base64.b64decode(image)
i = io.BytesIO(i)
i = mpimg.imread(i, format='PNG')

plt.imshow(i, interpolation='nearest')
plt.show()
```

#### JavaScript

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

const sandbox = await CodeInterpreter.create()

const code = `
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()
`;

// you can install dependencies in "jupyter notebook style"
await sandbox.notebook.execCell("!pip install matplotlib")

const execution = await sandbox.notebook.execCell(code)

// this contains the image data, you can e.g. save it to file or send to frontend
execution.results[0].png

await sandbox.close()
```

### Streaming code output

#### Python

```python
from e2b_code_interpreter import CodeInterpreter

code = """
import time
import pandas as pd

print("hello")
time.sleep(3)
data = pd.DataFrame(data=[[1, 2], [3, 4]], columns=["A", "B"])
display(data.head(10))
time.sleep(3)
print("world")
"""

with CodeInterpreter() as sandbox:
    sandbox.notebook.exec_cell(code, on_stdout=print, on_stderr=print, on_result=(lambda result: print(result.text)))

```

#### JavaScript

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

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

const sandbox = await CodeInterpreter.create()

await sandbox.notebook.execCell(code, {
  onStdout: (out) => console.log(out),
  onStderr: (outErr) => console.error(outErr),
  onResult: (result) => console.log(result.text)
})

await sandbox.close()
```

## How the SDK works
The code generated by LLMs is often split into code blocks, where each subsequent block references the previous one. This is a common pattern in Jupyter notebooks, where each cell can reference the variables and definitions from the previous cells. In the classical sandbox each code execution is independent and does not share the context with the previous executions.

This is suboptimal for a lot of Python use cases with LLMs. Especially GPT-3.5 and 4 expects it runs in a Jupyter Notebook environment. Even when ones tries to convince it otherwise. In practice, LLMs will generate code blocks which have references to previous code blocks. This becomes an issue if a user wants to execute each code block separately which often is the use case.

This new code interpreter template runs a Jupyter server inside the sandbox, which allows for sharing context between code executions.
Additionally, this new template also partly implements the [Jupyter Kernel messaging protocol](https://jupyter-client.readthedocs.io/en/latest/messaging.html). This means that, for example, support for plotting charts is now improved and we don't need to do hack-ish solutions like [in the current production version](https://github.com/e2b-dev/E2B/blob/main/sandboxes/code-interpreter/e2b_matplotlib_backend.py) of our code interpreter.

## Pre-installed Python packages inside the sandbox

The full and always up-to-date list can be found in the [`requirements.txt`](https://github.com/e2b-dev/E2B/blob/stateful-code-interpreter/sandboxes/code-interpreter-stateful/requirements.txt) file.

