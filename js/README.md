# Code interpreter extension for JavaScript

The repository contains a template and modules for the code interpreter sandbox. It is based on the Jupyter server and implements the Jupyter Kernel messaging protocol. This allows for sharing context between code executions and improves support for plotting charts and other display-able data.

## Key Features

- **Stateful Execution**: Unlike traditional sandboxes that treat each code execution independently, this package maintains context across executions.
- **Displaying Graph & Data**: Implements parts of the [Jupyter Kernel messaging protocol](https://jupyter-client.readthedocs.io/en/latest/messaging.html), which support for interactive features like plotting charts, rendering DataFrames, etc.

## Installation

```sh
npm install e2b_code_interpreter
```

## Examples

### Minimal example with the sharing context

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

const sandbox = await CodeInterpreter.create()
await sandbox.notebook.execCell('x = 1')

const result = await sandbox.notebook.execCell('x += 1; x')
console.log(result.text)  // outputs 2

await sandbox.close()
```

### Get charts and any display-able data

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
`

// you can install dependencies in "jupyter notebook style"
await sandbox.notebook.execCell("!pip install matplotlib")

const result = await sandbox.notebook.execCell(code)

// this contains the image data, you can e.g. save it to file or send to frontend
result.data[0].png

await sandbox.close()
```

### Streaming code output

```js
import { CodeInterpreter } from '@e2b/code-interpreter'

code = `
import time

print("hello")
time.sleep(5)
print("world")
`;

const sandbox = await CodeInterpreter.create()

await sandbox.notebook.execCell(
  code,
  (out) => console.log(out),
  (outErr) => console.error(outErr),
)
```

### Pre-installed Python packages inside the sandbox

The full and always up-to-date list can be found in the [`requirements.txt`](https://github.com/e2b-dev/E2B/blob/stateful-code-interpreter/sandboxes/code-interpreter-stateful/requirements.txt) file.

```text
# Jupyter server requirements
jupyter-server==2.13.0
ipykernel==6.29.3
ipython==8.22.2

# Other packages
aiohttp==3.9.3
beautifulsoup4==4.12.3
bokeh==3.3.4
gensim==4.3.2
imageio==2.34.0
joblib==1.3.2
librosa==0.10.1
matplotlib==3.8.3
nltk==3.8.1
numpy==1.26.4
opencv-python==4.9.0.80
openpyxl==3.1.2
pandas==1.5.3
plotly==5.19.0
pytest==8.1.0
python-docx==1.1.0
pytz==2024.1
requests==2.26.0
scikit-image==0.22.0
scikit-learn==1.4.1.post1
scipy==1.12.0
seaborn==0.13.2
soundfile==0.12.1
spacy==3.7.4
textblob==0.18.0
tornado==6.4
urllib3==1.26.7
xarray==2024.2.0
xlrd==2.0.1
```
