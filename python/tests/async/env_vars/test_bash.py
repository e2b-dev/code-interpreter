import pytest
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox
from typing import AsyncGenerator

@pytest.mark.skip_debug()
async def test_env_vars_on_sandbox():
    sandbox = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "echo $TEST_ENV_VAR",
            language="bash"
        )
        assert result.logs.stdout[0] == "supertest\n"
    finally:
        await sandbox.kill()

async def test_env_vars_per_execution(sandbox: AsyncSandbox):
    result = await sandbox.run_code(
        "echo $FOO",
        envs={"FOO": "bar"},
        language="bash"
    )
    
    result_empty = await sandbox.run_code(
        "echo ${FOO:-default}",
        language="bash"
    )
    
    assert result.logs.stdout[0] == "bar\n"
    assert result_empty.logs.stdout[0] == "default\n"

@pytest.mark.skip_debug()
async def test_env_vars_overwrite():
    sandbox = await AsyncSandbox.create(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "echo $TEST_ENV_VAR",
            language="bash",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        result_global_default = await sandbox.run_code(
            "echo $TEST_ENV_VAR",
            language="bash"
        )
        assert result.logs.stdout[0] == "overwrite\n"
        assert result_global_default.logs.stdout[0] == "supertest\n"
    finally:
        await sandbox.kill()
