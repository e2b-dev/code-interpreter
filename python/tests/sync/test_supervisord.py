import time

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


def test_restart_after_jupyter_kill(sandbox: Sandbox):
    # Verify health is up initially
    assert wait_for_health(sandbox)

    # Kill the jupyter process as root
    sandbox.commands.run("kill -9 $(pgrep -f 'jupyter server') || true", user="root")

    # Wait for supervisord to restart it and health to come back
    assert wait_for_health(sandbox, 20, 100)

    # Verify code execution works after recovery
    result = sandbox.run_code("x = 1; x")
    assert result.text == "1"


def test_restart_after_code_interpreter_kill(sandbox: Sandbox):
    # Verify health is up initially
    assert wait_for_health(sandbox)

    # Kill the code-interpreter process as root
    sandbox.commands.run(
        "kill -9 $(cat /var/run/code-interpreter.pid) || true", user="root"
    )

    # Wait for supervisord to restart it and health to come back
    assert wait_for_health(sandbox, 20, 100)

    # Verify code execution works after recovery
    result = sandbox.run_code("x = 1; x")
    assert result.text == "1"
