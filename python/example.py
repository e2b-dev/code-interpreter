from e2b_code_interpreter.main import CodeInterpreter
from dotenv import load_dotenv

load_dotenv()

python_code = """
k = 1
k
"""

java_code = """
(int) eval("1 + 1") + 3
"""

js_code = """
console.log("Hello World");
"""

r_code = """
x <- 13
x
"""

with CodeInterpreter() as sandbox:
    print(sandbox.id)

    execution = sandbox.notebook.exec_cell(python_code)
    print(execution)
    print(execution.logs)
    print(len(execution.results))

    js_id = sandbox.notebook.create_kernel(kernel_name="javascript")
    execution = sandbox.notebook.exec_cell(js_code, kernel_id=js_id)
    print(execution)
    print(execution.logs)
    print(len(execution.results))

    java_id = sandbox.notebook.create_kernel(kernel_name="java")
    execution = sandbox.notebook.exec_cell(java_code, kernel_id=java_id)
    print(execution)
    print(execution.logs)
    print(len(execution.results))


    r_id = sandbox.notebook.create_kernel(kernel_name="R")
    execution = sandbox.notebook.exec_cell(r_code, kernel_id=r_id)
    print(execution)
    print(execution.logs)
    print(len(execution.results))

