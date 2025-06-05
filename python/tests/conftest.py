import pytest
import pytest_asyncio
import os

from logging import warning

from e2b_code_interpreter.code_interpreter_async import AsyncSandbox
from e2b_code_interpreter.code_interpreter_sync import Sandbox

timeout = 60


@pytest.fixture()
def template():
    return os.getenv("E2B_TESTS_TEMPLATE", "code-interpreter-v1")


@pytest.fixture()
def sandbox(template, debug):
    sandbox = Sandbox(template, timeout=timeout)

    try:
        yield sandbox
    finally:
        try:
            sandbox.kill()
        except:
            if not debug:
                warning(
                    "Failed to kill sandbox — this is expected if the test runs with local envd."
                )


@pytest_asyncio.fixture
async def async_sandbox(template, debug):
    async_sandbox = await AsyncSandbox.create(template, timeout=timeout)

    try:
        yield async_sandbox
    finally:
        try:
            await async_sandbox.kill()
        except:
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
