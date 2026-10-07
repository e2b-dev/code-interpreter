import time

import httpx
import pytest

from harness import CodeInterpreter, CodeInterpreterError

pytestmark = pytest.mark.skip_debug


def wait_for_health(client: CodeInterpreter, max_retries=10, interval_ms=100) -> bool:
    for _ in range(max_retries):
        try:
            if client.health(timeout=5).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(interval_ms / 1000)
    return False


def kill_process(client: CodeInterpreter, pattern: str) -> None:
    # The request itself is expected to die with the process (killing jupyter
    # cascades to the code-interpreter service), so errors are ignored.
    try:
        client.run_code(f"!sudo kill -9 $(pgrep -f '{pattern}')", timeout=15)
    except (httpx.HTTPError, CodeInterpreterError):
        pass


def test_restart_after_jupyter_kill(client: CodeInterpreter):
    assert wait_for_health(client)

    kill_process(client, "jupyter server")

    # Wait for systemd to restart both services
    assert wait_for_health(client, 60, 500)

    execution = client.run_code("x = 1; x")
    assert execution.text == "1"


def test_restart_after_code_interpreter_kill(client: CodeInterpreter):
    assert wait_for_health(client)

    kill_process(client, "uvicorn main:app")

    # Wait for systemd to restart it and health to come back
    assert wait_for_health(client, 60, 500)

    execution = client.run_code("x = 1; x")
    assert execution.text == "1"
