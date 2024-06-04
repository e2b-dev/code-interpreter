from e2b_code_interpreter.main import CodeInterpreter
from dotenv import load_dotenv

load_dotenv()


code = """
(int) eval("1 + 1") + 3
"""

with CodeInterpreter(domain="e2b-api.com") as sandbox:
    print(sandbox.id)
    k_id = sandbox.notebook.create_kernel(kernel_name="java")
    execution = sandbox.notebook.exec_cell(code, kernel_id=k_id)

print(execution)
print(execution.logs)
print(len(execution.results))
