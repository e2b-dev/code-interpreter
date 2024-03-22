import time

from dotenv import load_dotenv

from e2b_code_interpreter.main import CodeInterpreter

load_dotenv()

iterations = 10
create_sandbox_time = 0
exec_python_x_equals_1_time = 0
exec_python_x_plus_equals_1_time = 0

for i in range(iterations):
    print('Iteration:', i + 1)
    start_time = time.time()
    sandbox = CodeInterpreter()
    create_sandbox_time += time.time() - start_time

    start_time = time.time()
    sandbox.notebook.exec_cell('x = 1')
    exec_python_x_equals_1_time += time.time() - start_time

    start_time = time.time()
    result = sandbox.notebook.exec_cell('x+=1; x')
    exec_python_x_plus_equals_1_time += time.time() - start_time

    sandbox.close()


print(f"Average Create Sandbox Time: {create_sandbox_time / iterations}s")
print(f"Average Execute Python x = 1 Time: {exec_python_x_equals_1_time / iterations}s")
print(f"Average Execute Python x+=1; x Time: {exec_python_x_plus_equals_1_time / iterations}s")
