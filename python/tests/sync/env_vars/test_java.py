import pytest
from e2b_code_interpreter import Sandbox

@pytest.mark.skip_debug()
def test_env_vars_on_sandbox():
    sandbox = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            "String x = System.getenv(\"TEST_ENV_VAR\"); x",
            language="java"
        )
        assert result.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()

def test_env_vars_per_execution():
    sandbox = Sandbox()
    try:
        result = sandbox.run_code(
            "System.getenv(\"FOO\")",
            envs={"FOO": "bar"},
            language="java"
        )
        
        result_empty = sandbox.run_code(
            "String value = System.getenv(\"FOO\"); value != null ? value : \"default\"",
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
            "String x = System.getenv(\"TEST_ENV_VAR\"); x",
            language="java",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        assert result.results[0].text.strip() == "overwrite"
    finally:
        sandbox.kill()
