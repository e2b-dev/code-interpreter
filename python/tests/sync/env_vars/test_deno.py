import pytest
from e2b_code_interpreter import Sandbox

@pytest.mark.skip_debug()
def test_env_vars_on_sandbox(template):
    sandbox = Sandbox(template=template, envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno"
        )
        assert result.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()

def test_env_vars_per_execution():
    sandbox = Sandbox()
    try:
        result = sandbox.run_code(
            "Deno.env.get('FOO')",
            envs={"FOO": "bar"},
            language="deno"
        )
        
        result_empty = sandbox.run_code(
            "Deno.env.get('FOO') || 'default'",
            language="deno"
        )
        
        assert result.results[0].text.strip() == "bar"
        assert result_empty.results[0].text.strip() == "default"
    finally:
        sandbox.kill()

@pytest.mark.skip_debug()
def test_env_vars_overwrite(template):
    sandbox = Sandbox(template=template, envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        result_global_default = sandbox.run_code(
            "const x = Deno.env.get('TEST_ENV_VAR'); x",
            language="deno"
        )
        assert result.results[0].text.strip() == "overwrite"
        assert result_global_default.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()
