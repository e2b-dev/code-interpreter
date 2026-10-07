# Code Interpreter HTTP tests

End-to-end tests for the Code Interpreter template, written against the server's
HTTP API on port `49999` with `httpx` only (no E2B SDK). Sandboxes are created
through the E2B control-plane API from `E2B_TESTS_TEMPLATE` (defaults to
`code-interpreter-v1`); see `.env.example` for configuration.

```bash
uv sync --locked
E2B_API_KEY=... uv run pytest
```

Set `E2B_DEBUG=true` to run against a local server started with
`make start-template-server`; tests marked `skip_debug` (sandbox provisioning,
optional kernels, recovery) are skipped in that mode.
