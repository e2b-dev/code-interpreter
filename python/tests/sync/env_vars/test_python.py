import pytest
from e2b_code_interpreter import Sandbox

@pytest.mark.skip_debug()
def test_env_vars_on_sandbox():
    sandbox = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sandbox.run_code(
            "import os; x = os.getenv('TEST_ENV_VAR'); x",
            language="python"
        )
        assert result.results[0].text.strip() == "supertest"
    finally:
        sandbox.kill()

def test_env_vars_per_execution():
    sandbox = Sandbox()
    try:
        result = sandbox.run_code(
            "import os; os.getenv('FOO')",
            envs={"FOO": "bar"}
        )
        
        result_empty = sandbox.run_code(
            "import os; os.getenv('FOO', 'default')",
            language="python"
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
            "import os; x = os.getenv('TEST_ENV_VAR'); x",
            language="python",
            envs={"TEST_ENV_VAR": "overwrite"}
        )
        assert result.results[0].text.strip() == "overwrite"
    finally:
        sandbox.kill()
