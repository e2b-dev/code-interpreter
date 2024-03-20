import time

from dotenv import load_dotenv

from e2b_code_interpreter.main import CodeInterpreter

load_dotenv()

iterations = 100
createSandboxTime = 0
exec_python_x_equals_1_time = 0
exec_python_x_plus_equals_1_time = 0

for i in range(iterations):
    print('Iteration:', i + 1)
    startTime = time.time()
    sandbox = CodeInterpreter()
    createSandboxTime += time.time() - startTime

    startTime = time.time()
    sandbox.notebook.exec_cell('x = 1')
    exec_python_x_equals_1_time += time.time() - startTime

    startTime = time.time()
    result = sandbox.notebook.exec_cell('x+=1; x')
    exec_python_x_plus_equals_1_time += time.time() - startTime

    sandbox.close()


print(f"Average Create Sandbox Time: {createSandboxTime / iterations}ms")
print(f"Average Execute Python x = 1 Time: {exec_python_x_equals_1_time / iterations}ms")
print(f"Average Execute Python x+=1; x Time: {exec_python_x_plus_equals_1_time / iterations}ms")
