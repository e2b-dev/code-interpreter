import asyncio
import time
from time import sleep

from dotenv import load_dotenv

from e2b_code_interpreter import AsyncCodeInterpreter

load_dotenv()


code = """
import psutil
import os

def force_oom():
    # Get current memory usage
    mem_before = psutil.virtual_memory().used
    
    # Start creating large lists
    size = 10000000  # Start with 10 million integers
    increment = 5000000  # Increase by 5 million integers each iteration
    
    while True:
        # Create a large list of integers
        large_list = [i for i in range(size)]
        
        # Get current memory usage
        mem_after = psutil.virtual_memory().used
        
        # Calculate memory difference
        mem_diff = mem_after - mem_before
        
        print(f"Created list of size {size} MB")
        print(f"Memory increase: {mem_diff / (1024 * 1024):.2f} GB")
        
        # Reset memory usage tracking
        mem_before = mem_after
        
        # Increment size for next iteration
        size += increment
        
        # Sleep briefly to allow OS to respond
        import time
        time.sleep(0.1)

# Run the function
force_oom()
"""


async def create_sbx(i: int):
    sbx = await AsyncCodeInterpreter.create(timeout=60, template="rth7a7wt20f3ymyr74zo")
    # with open('t2.csv') as f:
    #     await sbx.files.write("/home/user/t.csv", f)
    print("executing cell")
    print(f"Created sandbox {sbx.sandbox_id}")
    x = time.time()
    r = await sbx.notebook.exec_cell(code)
    print(f"Executed in {time.time() - x}")
    print(r.logs.stdout)
    print(r.error)


async def run():
    for j in range(1):
        print(f"Creating {j}. batch of sandboxes")
        futures = []
        for i in range(1):
            futures.append(create_sbx(i))

        sbxs = await asyncio.gather(*futures)
        sleep(2)


asyncio.run(run())
