from e2b_code_interpreter.code_interpreter_sync import CodeInterpreter


def test_create_new_kernel(sandbox: CodeInterpreter):
    sandbox.notebook.create_kernel()


def test_independence_of_kernels(sandbox: CodeInterpreter):
    kernel_id = sandbox.notebook.create_kernel()
    sandbox.notebook.exec_cell("x = 1")

    r = sandbox.notebook.exec_cell("x", kernel_id=kernel_id)
    assert r.error is not None
    assert r.error.value == "name 'x' is not defined"


def test_restart_kernel(sandbox: CodeInterpreter):
    sandbox.notebook.exec_cell("x = 1")
    sandbox.notebook.restart_kernel()

    r = sandbox.notebook.exec_cell("x")
    assert r.error is not None
    assert r.error.value == "name 'x' is not defined"


def test_list_kernels(sandbox: CodeInterpreter):
    kernels = sandbox.notebook.list_kernels()
    assert len(kernels) == 1

    kernel_id = sandbox.notebook.create_kernel()
    kernels = sandbox.notebook.list_kernels()
    assert kernel_id in kernels
    assert len(kernels) == 2


def test_shutdown(sandbox: CodeInterpreter):
    kernel_id = sandbox.notebook.create_kernel()
    kernels = sandbox.notebook.list_kernels()
    assert kernel_id in kernels
    assert len(kernels) == 2

    sandbox.notebook.shutdown_kernel(kernel_id)
    kernels = sandbox.notebook.list_kernels()
    assert kernel_id not in kernels
    assert len(kernels) == 1
