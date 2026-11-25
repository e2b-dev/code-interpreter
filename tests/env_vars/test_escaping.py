import json
import shlex

import pytest

from harness import CodeInterpreter


@pytest.mark.skip_debug
@pytest.mark.parametrize("language", ["python", "javascript", "typescript", "r", "java", "bash"])
@pytest.mark.parametrize("value", ["it's", 'a"b', "line1\nline2", r"C:\new\token"])
def test_env_literal_round_trip_and_cleanup(client: CodeInterpreter, language, value):
    # Bash requires identifier-shaped variable names; other kernels accept strings.
    key = "ESCAPED_TOKEN" if language == "bash" else "ESCAPED_'\"\\\n_TOKEN"
    key_literal, value_literal = json.dumps(key), json.dumps(value)
    checks = {
        "python": (
            f"import os; assert os.environ[{key!r}] == {value!r}",
            f"import os; assert {key!r} not in os.environ",
        ),
        "javascript": (
            f"if (process.env[{key_literal}] !== {value_literal}) throw Error('value');",
            f"if ({key_literal} in process.env) throw Error('cleanup');",
        ),
        "r": (
            f"stopifnot(Sys.getenv({key_literal}) == {value_literal})",
            f"stopifnot(is.na(Sys.getenv({key_literal}, unset=NA)))",
        ),
        "java": (
            f"if (!System.getProperty({key_literal}).equals({value_literal})) "
            'throw new RuntimeException("value");',
            f"if (System.getProperty({key_literal}) != null) "
            'throw new RuntimeException("cleanup");',
        ),
        "bash": (
            f'test "$ESCAPED_TOKEN" = {shlex.quote(value)} || echo VALUE_MISMATCH',
            'test "${ESCAPED_TOKEN+x}" != x || echo CLEANUP_FAILED',
        ),
    }
    checks["typescript"] = checks["javascript"]
    client.wait_for_kernel(language)
    check_value, check_cleanup = checks[language]
    execution = client.run_code(check_value, language=language, envs={key: value})
    assert execution.error is None
    assert not execution.stdout
    cleanup = client.run_code(check_cleanup, language=language)
    assert cleanup.error is None
    assert not cleanup.stdout
