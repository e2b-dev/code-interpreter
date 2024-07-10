import asyncio

from dotenv import load_dotenv

from e2b_code_interpreter import AsyncCodeInterpreter
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


async def run():
    sandbox = await AsyncCodeInterpreter.connect("", debug=True)
    print(sandbox.sandbox_id)
    execution = await sandbox.notebook.exec_cell(
        code,
        on_stdout=lambda msg: print("stdout", msg),
        on_stderr=lambda msg: print("stderr", msg),
    )

    print(execution.results[0].formats())
    print(len(execution.results))


asyncio.run(run())
