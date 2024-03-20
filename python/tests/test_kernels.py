from e2b_code_interpreter.main import CodeInterpreter


def test_create_new_kernel():
    with CodeInterpreter() as sandbox:
        sandbox.notebook.create_kernel()


def test_independence_of_kernels():
    with CodeInterpreter() as sandbox:
        kernel_id = sandbox.notebook.create_kernel()
        sandbox.notebook.exec_cell("x = 1")

        r = sandbox.notebook.exec_cell("x", kernel_id=kernel_id)
        assert r.error.value == "name 'x' is not defined"


def test_restart_kernel():
    with CodeInterpreter() as sandbox:
        sandbox.notebook.exec_cell("x = 1")
        sandbox.notebook.restart_kernel()

        r = sandbox.notebook.exec_cell("x")
        assert r.error.value == "name 'x' is not defined"


def test_list_kernels():
    with CodeInterpreter() as sandbox:
        kernels = sandbox.notebook.list_kernels()
        assert len(kernels) == 1

        kernel_id = sandbox.notebook.create_kernel()
        kernels = sandbox.notebook.list_kernels()
        assert kernel_id in kernels
        assert len(kernels) == 2
