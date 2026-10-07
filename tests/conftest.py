import os
import uuid
from typing import Callable, Optional

import pytest
from dotenv import load_dotenv

from harness import AsyncCodeInterpreter, CodeInterpreter, SandboxApi, SandboxInfo

load_dotenv()

DEFAULT_TEST_SANDBOX_TIMEOUT = 120
LOCAL_SERVER_URL = "http://localhost:49999"


def is_debug() -> bool:
    return os.getenv("E2B_DEBUG", "false").lower() == "true"


@pytest.fixture(scope="session")
def sandbox_test_id() -> str:
    return f"test_{uuid.uuid4()}"


@pytest.fixture(scope="session")
def template() -> str:
    return os.getenv("E2B_TESTS_TEMPLATE") or "code-interpreter-v1"


@pytest.fixture(scope="session")
def sandbox_api() -> SandboxApi:
    api = SandboxApi(
        api_key=os.environ["E2B_API_KEY"],
        domain=os.getenv("E2B_DOMAIN") or "e2b.app",
    )
    yield api
    api.close()


@pytest.fixture()
def sandbox_factory(
    request: pytest.FixtureRequest, template: str, sandbox_test_id: str
) -> Callable[..., SandboxInfo]:
    if is_debug():
        pytest.skip("Sandbox provisioning is not available in debug mode")

    api: SandboxApi = request.getfixturevalue("sandbox_api")

    def factory(
        *,
        timeout: int = DEFAULT_TEST_SANDBOX_TIMEOUT,
        envs: Optional[dict[str, str]] = None,
        allow_public_traffic: bool = True,
    ) -> SandboxInfo:
        sandbox = api.create(
            template,
            timeout=timeout,
            metadata={"sandbox_test_id": sandbox_test_id},
            envs=envs,
            allow_public_traffic=allow_public_traffic,
        )
        request.addfinalizer(lambda: api.kill(sandbox.sandbox_id))
        return sandbox

    return factory


@pytest.fixture()
def sandbox(sandbox_factory) -> SandboxInfo:
    return sandbox_factory()


def make_client(sandbox: SandboxInfo) -> CodeInterpreter:
    return CodeInterpreter(
        sandbox.code_interpreter_url,
        envd_access_token=sandbox.envd_access_token,
        traffic_access_token=sandbox.traffic_access_token,
    )


def make_async_client(sandbox: SandboxInfo) -> AsyncCodeInterpreter:
    return AsyncCodeInterpreter(
        sandbox.code_interpreter_url,
        envd_access_token=sandbox.envd_access_token,
        traffic_access_token=sandbox.traffic_access_token,
    )


@pytest.fixture()
def client_factory(request: pytest.FixtureRequest, sandbox_factory):
    def factory(**sandbox_kwargs) -> CodeInterpreter:
        client = make_client(sandbox_factory(**sandbox_kwargs))
        request.addfinalizer(client.close)
        return client

    return factory


@pytest.fixture()
def client(request: pytest.FixtureRequest, client_factory) -> CodeInterpreter:
    if is_debug():
        client = CodeInterpreter(LOCAL_SERVER_URL)
        request.addfinalizer(client.close)
        return client
    return client_factory()


@pytest.fixture()
async def async_client(request: pytest.FixtureRequest, sandbox_factory):
    if is_debug():
        client = AsyncCodeInterpreter(LOCAL_SERVER_URL)
    else:
        client = make_async_client(sandbox_factory())
    yield client
    await client.aclose()


@pytest.fixture()
def java_client(client: CodeInterpreter) -> CodeInterpreter:
    client.wait_for_kernel("java")
    return client


@pytest.fixture(autouse=True)
def skip_debug(request: pytest.FixtureRequest):
    if request.node.get_closest_marker("skip_debug") and is_debug():
        pytest.skip("Skipped in debug mode")
