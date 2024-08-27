import asyncio

from dotenv import load_dotenv

from e2b_code_interpreter import AsyncCodeInterpreter

load_dotenv()


code = """
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

x = np.linspace(0, 20, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()


class Test():
    def _repr_e2b_data_(self):
        return {"a": 1}

Test()
"""


async def run():
    sandbox = await AsyncCodeInterpreter.connect("", debug=True)
    print(sandbox.sandbox_id)
    execution = await sandbox.notebook.exec_cell(code)

    print('\n'.join(execution.logs.stdout))
    print('\n'.join(execution.logs.stderr))
    if execution.error:
        print(execution.error.traceback)
    print(len(execution.results))
    print(execution.results[0].formats())
    print(execution.results[1].formats())


asyncio.run(run())
