import pytest_asyncio

from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


@pytest_asyncio.fixture
async def test_create_new_kernel(async_sandbox: AsyncCodeInterpreter):
    await async_sandbox.notebook.create_kernel()


@pytest_asyncio.fixture
async def test_independence_of_kernels(async_sandbox: AsyncCodeInterpreter):
    kernel_id = await async_sandbox.notebook.create_kernel()
    await async_sandbox.notebook.exec_cell("x = 1")

    r = await async_sandbox.notebook.exec_cell("x", kernel_id=kernel_id)
    assert r.error.value == "name 'x' is not defined"


@pytest_asyncio.fixture
async def test_restart_kernel(async_sandbox: AsyncCodeInterpreter):
    await async_sandbox.notebook.exec_cell("x = 1")
    await async_sandbox.notebook.restart_kernel()

    r = await async_sandbox.notebook.exec_cell("x")
    assert r.error.value == "name 'x' is not defined"


@pytest_asyncio.fixture
async def test_list_kernels(async_sandbox: AsyncCodeInterpreter):
    kernels = await async_sandbox.notebook.list_kernels()
    assert len(kernels) == 1

    kernel_id = await async_sandbox.notebook.create_kernel()
    kernels = await async_sandbox.notebook.list_kernels()
    assert kernel_id in kernels
    assert len(kernels) == 2


@pytest_asyncio.fixture
async def test_shutdown(async_sandbox: AsyncCodeInterpreter):
    kernel_id = await async_sandbox.notebook.create_kernel()
    kernels = await async_sandbox.notebook.list_kernels()
    assert kernel_id in kernels
    assert len(kernels) == 2

    await async_sandbox.notebook.shutdown_kernel(kernel_id)
    kernels = await async_sandbox.notebook.list_kernels()
    assert kernel_id not in kernels
    assert len(kernels) == 1
