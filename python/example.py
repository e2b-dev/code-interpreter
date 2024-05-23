from e2b_code_interpreter.main import CodeInterpreter
from dotenv import load_dotenv

load_dotenv()


code = """
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
"""

with CodeInterpreter() as sandbox:
    result = sandbox.notebook.exec_cell(code)

print(result.results[0].formats())
print(len(result.results))
