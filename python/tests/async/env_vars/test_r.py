import pytest
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox

@pytest.mark.skip_debug()
async def test_env_vars_on_sandbox():
    sandbox = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "Sys.getenv('TEST_ENV_VAR')",
            language="r"
        )
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sandbox.kill()

async def test_env_vars_per_execution():
    sandbox = await AsyncSandbox.create()
    try:
        result = await sandbox.run_code(
            "Sys.getenv('FOO')",
            envs={"FOO": "bar"},
            language="r"
        )
        
        result_empty = await sandbox.run_code(
            "Sys.getenv('FOO', unset = 'default')",
            language="r"
        )
        
        assert result.text is not None
        assert result.text.strip() == "bar"
        assert result_empty.text is not None
        assert result_empty.text.strip() == "default"
    finally:
        await sandbox.kill()

@pytest.mark.skip_debug()
async def test_env_vars_overwrite():
    sandbox = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "Sys.getenv('TEST_ENV_VAR')",
            language="r",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        assert result.text is not None
        assert result.text.strip() == "overwrite"
    finally:
        await sandbox.kill()
