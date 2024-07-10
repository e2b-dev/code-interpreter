from dotenv import load_dotenv
from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter

load_dotenv()


code = """
import matplotlib.pyplot as plt
import numpy as np
import time

print("1")
time.sleep(10)

import pandas
pandas.DataFrame({"a": [1, 2, 3]})
"""

sandbox = CodeInterpreter.connect("", debug=True)
sandbox.notebook.exec_cell("x = 1")
sandbox.notebook.restart_kernel()

r = sandbox.notebook.exec_cell("x")
assert r.error.value == "name 'x' is not defined"
