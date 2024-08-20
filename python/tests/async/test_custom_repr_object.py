from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter

code = """
from IPython.display import display

display({'text/latex': r'\text{CustomReprObject}'}, raw=True)
"""


async def test_bash(sandbox: AsyncCodeInterpreter):
    execution = await sandbox.notebook.exec_cell(code)
    assert execution.results[0].formats() == ["latex"]
