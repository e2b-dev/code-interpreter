import pytest
from e2b_code_interpreter import Sandbox

@pytest.mark.skip_debug()
def test_env_vars_on_sandbox():
    sandbox = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            'System.getProperty("TEST_ENV_VAR")',
            language="java"
        )
        assert result.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()

def test_env_vars_per_execution():
    sandbox = Sandbox()
    try:
        result = sandbox.run_code(
            'System.getProperty("FOO")',
            envs={"FOO": "bar"},
            language="java"
        )
        
        result_empty = sandbox.run_code(
            'System.getProperty("FOO", "default")',
            language="java"
        )
        
        assert result.results[0].text.strip() == "bar"
        assert result_empty.results[0].text.strip() == "default"
    finally:
        sandbox.kill()

@pytest.mark.skip_debug()
def test_env_vars_overwrite():
    sandbox = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            'System.getProperty("TEST_ENV_VAR")',
            language="java",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        result_global_default = sandbox.run_code(
            'System.getProperty("TEST_ENV_VAR")',
            language="java"
        )
        assert result.results[0].text.strip() == "overwrite"
        assert result_global_default.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()
