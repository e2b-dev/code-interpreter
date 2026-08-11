---
'@e2b/code-interpreter': patch
'@e2b/code-interpreter-python': patch
---

Bump the E2B SDK dependency: JavaScript to 2.38.3, Python to 2.38.0.

The Python SDK moved its HTTP stack onto [`pyqwest`](https://pypi.org/project/pyqwest/), and its internal `get_transport()` helper no longer takes an `http2` argument — the HTTP version is negotiated by ALPN instead, which means HTTP/2 against the sandbox. Jupyter requests build their own HTTP/1.1 transport now (`e2b_code_interpreter.transport`), from the same pool tuning and connect-only retry policy the SDK uses, so client disconnects keep propagating to the server as a TCP close and long-running executions stay reliably cancellable.
