import pytest

from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


@pytest.mark.skip_debug()
async def test_env_vars_sandbox():
    sbx = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sbx.run_code("import os; os.getenv('TEST_ENV_VAR')")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sbx.kill()


async def test_env_vars_in_run_code(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(
        "import os; os.getenv('FOO')", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# JavaScript tests
@pytest.mark.skip_debug()
async def test_env_vars_javascript_sandbox():
    sbx = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sbx.run_code("process.env.TEST_ENV_VAR")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sbx.kill()


async def test_env_vars_javascript(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(
        "process.env.FOO", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# R tests
@pytest.mark.skip_debug()
async def test_env_vars_r_sandbox():
    sbx = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sbx.run_code('Sys.getenv("TEST_ENV_VAR")')
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sbx.kill()


async def test_env_vars_r(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(
        'Sys.getenv("FOO")', envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# Java tests
@pytest.mark.skip_debug()
async def test_env_vars_java_sandbox():
    sbx = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sbx.run_code('System.getenv("TEST_ENV_VAR")')
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sbx.kill()


async def test_env_vars_java(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(
        'System.getenv("FOO")', envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# Bash tests
@pytest.mark.skip_debug()
async def test_env_vars_bash_sandbox():
    sbx = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sbx.run_code("echo $TEST_ENV_VAR")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sbx.kill()


async def test_env_vars_bash(async_sandbox: AsyncSandbox):
    result = await async_sandbox.run_code(
        "echo $FOO", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"
