---
'@e2b/code-interpreter': minor
'@e2b/code-interpreter-python': minor
---

Honor the `sandboxUrl`/`sandbox_url` option and the `E2B_SANDBOX_URL` environment variable when connecting to the Jupyter server, matching the base E2B SDK. Jupyter requests now also send the `E2b-Sandbox-Id` and `E2b-Sandbox-Port` headers so a custom sandbox URL (e.g. a gateway or proxy) can route them to the right sandbox and port.
