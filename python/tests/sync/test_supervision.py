import time

import pytest

from e2b_code_interpreter.code_interpreter_sync import Sandbox


def wait_for_health(sandbox: Sandbox, max_retries=10, interval_ms=100):
    for _ in range(max_retries):
        try:
            result = sandbox.commands.run(
                'curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:49999/health'
            )
            if result.stdout.strip() == "200":
                return True
        except Exception:
            pass
        time.sleep(interval_ms / 1000)
    return False


def wait_for_working_sandbox(sandbox: Sandbox, max_retries=60, interval_ms=500):
    """Recovery has to be judged by running code, not by /health.

    Killing Jupyter leaves the code-interpreter server up but holding dead
    kernel handles, so it answers /health for a few seconds before the process
    manager recycles it — long enough for a health check to pass against a
    sandbox that cannot execute.
    """
    for _ in range(max_retries):
        try:
            result = sandbox.run_code("x = 1; x")
            if result.text == "1":
                return True
        except Exception:
            pass
        time.sleep(interval_ms / 1000)
    return False


@pytest.mark.skip_debug
def test_restart_after_jupyter_kill(sandbox: Sandbox):
    # Verify health is up initially
    assert wait_for_health(sandbox)

    # Kill the jupyter process as root. The pattern is bracketed so it cannot
    # match the shell running it — `pgrep -f 'jupyter server'` matched its own
    # command line, so this only ever killed itself. pkill exits non-zero when
    # nothing matched, which fails the test rather than passing it vacuously.
    sandbox.commands.run("pkill -9 -f '[j]upyter-server'", user="root")

    # Wait for process-compose to restart both processes
    assert wait_for_working_sandbox(sandbox)


@pytest.mark.skip_debug
def test_restart_after_code_interpreter_kill(sandbox: Sandbox):
    # Verify health is up initially
    assert wait_for_health(sandbox)

    # Kill the code-interpreter process as root
    sandbox.commands.run("pkill -9 -f '[u]vicorn main:app'", user="root")

    # Wait for process-compose to restart it
    assert wait_for_working_sandbox(sandbox)
