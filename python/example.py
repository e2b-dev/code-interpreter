from dotenv import load_dotenv
from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter

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

sandbox = CodeInterpreter.connect("", debug=True)
print(sandbox.sandbox_id)
execution = sandbox.notebook.exec_code(
    code,
    on_stdout=lambda msg: print("stdout", msg),
    on_stderr=lambda msg: print("stderr", msg),
)

print(execution.results[0].formats())
print(len(execution.results))
