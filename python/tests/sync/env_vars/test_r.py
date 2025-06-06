import pytest
from e2b_code_interpreter import Sandbox

@pytest.mark.skip_debug()
def test_env_vars_on_sandbox():
    sandbox = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            "Sys.getenv('TEST_ENV_VAR')",
            language="r"
        )
        assert result.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()

def test_env_vars_per_execution():
    sandbox = Sandbox()
    try:
        result = sandbox.run_code(
            "Sys.getenv('FOO')",
            envs={"FOO": "bar"},
            language="r"
        )
        
        result_empty = sandbox.run_code(
            "Sys.getenv('FOO', unset = 'default')",
            language="r"
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
            "Sys.getenv('TEST_ENV_VAR')",
            language="r",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        assert result.results[0].text.strip() == "overwrite"
    finally:
        sandbox.kill()
