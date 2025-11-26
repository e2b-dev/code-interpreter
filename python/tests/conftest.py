import asyncio
import os

import pytest

from e2b_code_interpreter import (
    AsyncSandbox,
    Sandbox,
)
import uuid


@pytest.fixture(scope="session")
def sandbox_test_id():
    return f"test_{uuid.uuid4()}"


@pytest.fixture()
def template():
    return os.getenv("E2B_TESTS_TEMPLATE") or "code-interpreter-v1"


@pytest.fixture()
def sandbox_factory(request, template, sandbox_test_id):
    def factory(*, template_name: str = template, **kwargs):
        kwargs.setdefault("secure", False)
        kwargs.setdefault("timeout", 5)

        metadata = kwargs.setdefault("metadata", dict())
        metadata.setdefault("sandbox_test_id", sandbox_test_id)

        sandbox = Sandbox.create(template_name, **kwargs)

        request.addfinalizer(lambda: sandbox.kill())

        return sandbox

    return factory


@pytest.fixture()
def sandbox(sandbox_factory):
    return sandbox_factory()


# override the event loop so it never closes
# this helps us with the global-scoped async http transport
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_sandbox_factory(request, template, sandbox_test_id, event_loop):
    async def factory(*, template_name: str = template, **kwargs):
        kwargs.setdefault("timeout", 5)

        metadata = kwargs.setdefault("metadata", dict())
        metadata.setdefault("sandbox_test_id", sandbox_test_id)

        sandbox = await AsyncSandbox.create(template_name, **kwargs)

        def kill():
            async def _kill():
                await sandbox.kill()

            event_loop.run_until_complete(_kill())

        request.addfinalizer(kill)

        return sandbox

    return factory


@pytest.fixture
async def async_sandbox(async_sandbox_factory):
    return await async_sandbox_factory()


@pytest.fixture
def debug():
    return os.getenv("E2B_DEBUG") is not None


@pytest.fixture(autouse=True)
def skip_by_debug(request, debug):
    if request.node.get_closest_marker("skip_debug"):
        if debug:
            pytest.skip("skipped because E2B_DEBUG is set")
