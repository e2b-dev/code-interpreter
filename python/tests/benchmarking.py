import time

from dotenv import load_dotenv

from e2b_code_interpreter.code_interpreter_sync import Sandbox

load_dotenv()

iterations = 10
create_sandbox_time = 0
first_exec_time = 0
second_exec_time = 0

for i in range(iterations):
    print("Iteration:", i + 1)
    start_time = time.time()
    sandbox = Sandbox()
    create_sandbox_time += time.time() - start_time

    start_time = time.time()
    sandbox.notebook.exec_cell("x = 1")
    first_exec_time += time.time() - start_time

    start_time = time.time()
    result = sandbox.notebook.exec_cell("x+=1; x")
    second_exec_time += time.time() - start_time

    sandbox.close()


print(f"Average Create Sandbox Time: {create_sandbox_time / iterations}s")
print(f"Average Execute Python x = 1 Time: {first_exec_time / iterations}s")
print(f"Average Execute Python x+=1; x Time: {second_exec_time / iterations}s")
