import pytest

from e2b_code_interpreter.code_interpreter_sync import Sandbox


@pytest.mark.skip_debug()
def test_env_vars_sandbox():
    sbx = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sbx.run_code("import os; os.getenv('TEST_ENV_VAR')")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        sbx.kill()


def test_env_vars_in_run_code(sandbox: Sandbox):
    result = sandbox.run_code(
        "import os; os.getenv('FOO')", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# JavaScript tests
@pytest.mark.skip_debug()
def test_env_vars_javascript_sandbox():
    sbx = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sbx.run_code("process.env.TEST_ENV_VAR")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        sbx.kill()


def test_env_vars_javascript(sandbox: Sandbox):
    result = sandbox.run_code(
        "process.env.FOO", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# R tests
@pytest.mark.skip_debug()
def test_env_vars_r_sandbox():
    sbx = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sbx.run_code('Sys.getenv("TEST_ENV_VAR")')
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        sbx.kill()


def test_env_vars_r(sandbox: Sandbox):
    result = sandbox.run_code(
        'Sys.getenv("FOO")', envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# Java tests
@pytest.mark.skip_debug()
def test_env_vars_java_sandbox():
    sbx = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sbx.run_code('System.getenv("TEST_ENV_VAR")')
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        sbx.kill()


def test_env_vars_java(sandbox: Sandbox):
    result = sandbox.run_code(
        'System.getenv("FOO")', envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"


# Bash tests
@pytest.mark.skip_debug()
def test_env_vars_bash_sandbox():
    sbx = Sandbox(envs={"TEST_ENV_VAR": "supertest"})
    try:
        result = sbx.run_code("echo $TEST_ENV_VAR")
        assert result.text is not None
        assert result.text.strip() == "supertest"
    finally:
        sbx.kill()


def test_env_vars_bash(sandbox: Sandbox):
    result = sandbox.run_code(
        "echo $FOO", envs={"FOO": "bar"}
    )
    assert result.text is not None
    assert result.text.strip() == "bar"
