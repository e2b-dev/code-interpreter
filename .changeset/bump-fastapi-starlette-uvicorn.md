---
'@e2b/code-interpreter-template': patch
---

Upgrade the interpreter server to `fastapi==0.162.0` (Starlette 1.10.0), `uvicorn[standard]==0.54.0` and `websockets==17.3`. The previous `fastapi==0.111.0` pin pulled in Starlette 0.37.2, which is affected by CVE-2024-47874. Upgrading Starlette alone would break kernel interrupts on client disconnect (`run_code` timeouts): uvicorn 0.30.1 advertises ASGI spec 2.4 without raising on writes to a closed connection, so Starlette >= 0.42 never cancels the streaming body and the timed-out cell keeps running in the kernel; uvicorn >= 0.32.1 reports spec 2.3 again, so disconnects cancel the stream and the kernel is interrupted.
