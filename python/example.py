import logging

from e2b_code_interpreter.main import CodeInterpreter
from dotenv import load_dotenv
load_dotenv()

with CodeInterpreter() as sandbox:
    result = sandbox.notebook.exec_cell("x =1; x")
    assert result.output == "1"

print(result)
