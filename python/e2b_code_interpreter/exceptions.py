from e2b import TimeoutException


def format_request_timeout_error() -> Exception:
    return TimeoutException(
        f"Request timed out — the 'request_timeout' option can be used to increase this timeout",
    )


def format_execution_timeout_error() -> Exception:
    return TimeoutException(
        f"Execution timed out — the 'timeout' option can be used to increase this timeout",
    )
