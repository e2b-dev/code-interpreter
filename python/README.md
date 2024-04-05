# Code interpreter extension for Python

The repository contains a template and modules for the code interpreter sandbox. It is based on the Jupyter server and implements the Jupyter Kernel messaging protocol. This allows for sharing context between code executions and improves support for plotting charts and other display-able data.

## Key Features

- **Stateful Execution**: Unlike traditional sandboxes that treat each code execution independently, this package maintains context across executions.
- **Displaying Graph & Data**: Implements parts of the [Jupyter Kernel messaging protocol](https://jupyter-client.readthedocs.io/en/latest/messaging.html), which support for interactive features like plotting charts, rendering DataFrames, etc.

## Installation

```sh
pip install e2b-code-interpreter
```

## Examples

### Minimal example with the sharing context

```python
from e2b_code_interpreter import CodeInterpreter

with CodeInterpreter() as sandbox:
    sandbox.notebook.exec_cell("x = 1")

    execution = sandbox.notebook.exec_cell("x+=1; x")
    print(execution.text)  # outputs 2

```

### Get charts and any display-able data

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

### Streaming code output

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
