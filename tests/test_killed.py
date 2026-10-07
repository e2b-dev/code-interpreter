import threading
import time

import httpx
import pytest

from conftest import make_client
from harness import Execution, SandboxApi, SandboxInfo


@pytest.mark.skip_debug
def test_execution_ends_when_sandbox_is_killed(
    sandbox: SandboxInfo, sandbox_api: SandboxApi
):
    client = make_client(sandbox)
    timer = threading.Timer(2.0, sandbox_api.kill, args=[sandbox.sandbox_id])
    timer.start()

    execution = Execution()
    started = time.monotonic()
    try:
        # The sleep is far longer than the kill delay, so the only thing that
        # can end the request is the sandbox being killed.
        with pytest.raises(httpx.HTTPError):
            for event in client.stream_code(
                "import time; time.sleep(300)", timeout=300
            ):
                execution.add(event)
    finally:
        timer.cancel()
        client.close()

    assert time.monotonic() - started < 60
    assert not execution.completed
    assert sandbox_api.get(sandbox.sandbox_id) is None
