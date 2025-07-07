import pytest
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox

@pytest.mark.skip_debug()
async def test_env_vars_on_sandbox(template):
    sandbox = await AsyncSandbox.create(template=template, envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno"
        )
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        await sandbox.kill()

async def test_env_vars_per_execution(sandbox: AsyncSandbox, template):
    sandbox = await AsyncSandbox.create(template=template)
    result = await sandbox.run_code(
        "Deno.env.get('FOO')",
        envs={"FOO": "bar"},
        language="deno"
    )
    
    result_empty = await sandbox.run_code(
        "Deno.env.get('FOO') || 'default'",
        language="deno"
    )
    
    assert result.text is not None
    assert result.text.strip() == "bar"
    assert result_empty.text is not None
    assert result_empty.text.strip() == "default"

@pytest.mark.skip_debug()
async def test_env_vars_overwrite(template):
    sandbox = await AsyncSandbox.create(template=template, envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = await sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        result_global_default = await sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno"
        )
        assert result.text is not None
        assert result.text.strip() == "overwrite"
        assert result_global_default.text is not None
        assert result_global_default.text.strip() == "supertest"
    finally:
        await sandbox.kill()
