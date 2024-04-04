from e2b_code_interpreter.main import CodeInterpreter


def test_streaming_output():
    out = []
    with CodeInterpreter() as sandbox:

        def test(line) -> int:
            out.append(line)
            return 1

        sandbox.notebook.exec_cell("print(1)", on_stdout=test)

    assert len(out) == 1
    assert out[0].line == "1\n"


def test_streaming_error():
    out = []
    with CodeInterpreter() as sandbox:
        sandbox.notebook.exec_cell(
            "import sys;print(1, file=sys.stderr)", on_stderr=out.append
        )

    assert len(out) == 1
    assert out[0].line == "1\n"


def test_streaming_result():
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
    with CodeInterpreter() as sandbox:
        sandbox.notebook.exec_cell(code, on_result=out.append)

    assert len(out) == 2
