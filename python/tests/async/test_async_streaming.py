from e2b_code_interpreter.code_interpreter_async import AsyncCodeInterpreter


async def test_streaming_output(async_sandbox: AsyncCodeInterpreter):
    out = []

    def test(line) -> None:
        out.append(line)
        return

    await async_sandbox.notebook.exec_cell("print(1)", on_stdout=test)

    assert len(out) == 1
    assert out[0].line == "1\n"


async def test_streaming_error(async_sandbox: AsyncCodeInterpreter):
    out = []

    await async_sandbox.notebook.exec_cell(
        "import sys;print(1, file=sys.stderr)", on_stderr=out.append
    )

    assert len(out) == 1
    assert out[0].line == "1\n"


async def test_streaming_result(async_sandbox: AsyncCodeInterpreter):
    code = """
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.linspace(0, 20, 100)
    y = np.sin(x)

    plt.plot(x, y)
    plt.show()
    
    x
    """

    out = []
    await async_sandbox.notebook.exec_cell(code, on_result=out.append)

    assert len(out) == 2
