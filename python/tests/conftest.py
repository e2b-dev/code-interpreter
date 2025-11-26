import pytest
import pytest_asyncio
import os
import asyncio

from logging import warning

from e2b_code_interpreter.code_interpreter_async import AsyncSandbox
from e2b_code_interpreter.code_interpreter_sync import Sandbox

timeout = 60


# Override the event loop so it never closes during test execution
# This helps with pytest-xdist and prevents "Event loop is closed" errors
@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for all async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def template():
    return os.getenv("E2B_TESTS_TEMPLATE") or "code-interpreter-v1"


@pytest.fixture()
def sandbox(template, debug, network):
    sandbox = Sandbox.create(template, timeout=timeout, debug=debug, network=network)

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


@pytest.fixture
def async_sandbox_factory(request, template, debug, network, event_loop):
    """Factory for creating async sandboxes with proper cleanup."""

    async def factory(template_override=None, **kwargs):
        template_name = template_override or template
        kwargs.setdefault("timeout", timeout)
        kwargs.setdefault("debug", debug)
        sandbox = await AsyncSandbox.create(template_name, network=network, **kwargs)

        def kill():
            async def _kill():
                try:
                    await sandbox.kill()
                except:  # noqa: E722
                    if not debug:
                        warning(
                            "Failed to kill sandbox — this is expected if the test runs with local envd."
                        )

            event_loop.run_until_complete(_kill())

        request.addfinalizer(kill)
        return sandbox

    return factory


@pytest.fixture
async def async_sandbox(async_sandbox_factory):
    """Default async sandbox fixture."""
    return await async_sandbox_factory()


@pytest.fixture
def debug():
    return os.getenv("E2B_DEBUG") is not None


@pytest.fixture(autouse=True)
def skip_by_debug(request, debug):
    if request.node.get_closest_marker("skip_debug"):
        if debug:
            pytest.skip("skipped because E2B_DEBUG is set")
