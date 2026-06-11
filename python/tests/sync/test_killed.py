import threading

import pytest

from e2b import SandboxException
from e2b_code_interpreter import Sandbox


@pytest.mark.skip_debug
def test_run_code_raises_when_sandbox_is_killed_during_execution(sandbox: Sandbox):
    timer = threading.Timer(2.0, sandbox.kill)
    timer.start()

    try:
        with pytest.raises(
            SandboxException,
            match="sandbox was killed while the request was in progress",
        ):
            sandbox.run_code("import time; time.sleep(60)")
    finally:
        timer.cancel()
