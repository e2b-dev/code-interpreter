import pytest
import pytest_asyncio
import os
import asyncio

from logging import warning

from e2b_code_interpreter.code_interpreter_async import AsyncSandbox
from e2b_code_interpreter.code_interpreter_sync import Sandbox

timeout = 60


@pytest_asyncio.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    # Clean up any remaining tasks
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    # Close the loop gracefully
    try:
        loop.close()
    except Exception:
        pass


@pytest.fixture()
def template():
    return os.getenv("E2B_TESTS_TEMPLATE") or "code-interpreter-v1"


@pytest.fixture()
def sandbox(template, debug):
    sandbox = Sandbox.create(template, timeout=timeout, debug=debug)

    try:
        yield sandbox
    finally:
        try:
            sandbox.kill()
        except:  # noqa: E722
            if not debug:
                warning(
                    "Failed to kill sandbox — this is expected if the test runs with local envd."
                )


@pytest_asyncio.fixture(loop_scope="function")
async def async_sandbox(template, debug):
    async_sandbox = await AsyncSandbox.create(template, timeout=timeout, debug=debug)

    try:
        yield async_sandbox
    finally:
        try:
            await async_sandbox.kill()
        except RuntimeError as e:
            # Ignore "Event loop is closed" errors during cleanup in pytest-xdist
            if "Event loop is closed" not in str(e):
                raise
        except:  # noqa: E722
            if not debug:
                warning(
                    "Failed to kill sandbox — this is expected if the test runs with local envd."
                )


@pytest.fixture
def debug():
    return os.getenv("E2B_DEBUG") is not None


@pytest.fixture(autouse=True)
def skip_by_debug(request, debug):
    if request.node.get_closest_marker("skip_debug"):
        if debug:
            pytest.skip("skipped because E2B_DEBUG is set")
