---
'@e2b/code-interpreter': patch
'@e2b/code-interpreter-python': patch
---

Bump E2B SDK dependency: JavaScript to 2.39.0, Python to 2.39.1.

The Python floor is 2.39.1 specifically: e2b 2.38.0 moved the SDK's HTTP stack onto [`pyqwest`](https://pypi.org/project/pyqwest/) and dropped the `http2` parameter that Jupyter requests rely on to pin HTTP/1.1, so any e2b in `>=2.38.0, <2.39.1` raises `TypeError` on every code execution. 2.39.1 restores it.
