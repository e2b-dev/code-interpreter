from e2b_code_interpreter.main import CodeInterpreter
from dotenv import load_dotenv

load_dotenv()


code = """class Welcome:
    def _repr_html_(self):
        return "<h1>Welcome to the code interpreter!</h1>"
Welcome()
"""

graph = """import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()

import pandas
pandas.DataFrame({"a": [1, 2, 3]})
"""

with CodeInterpreter(template="code-interpreter-stateful-lab") as sandbox:
    print(f"https://{sandbox.get_hostname(8888)}/doc/tree/RTC:default.ipynb")
    sandbox.notebook.exec_cell(code)
    sandbox.notebook.exec_cell(graph)
    while True:
        r = sandbox.notebook.exec_cell(input("code: "))
        if r.results:
            print(r.results[0].text)
