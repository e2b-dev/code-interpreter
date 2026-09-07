---
'@e2b/code-interpreter-template': patch
---

Interrupt the kernel when the HTTP client disconnects mid-execution so the per-context lock is released and subsequent executions aren't blocked (#213). On the latest FastAPI (0.136.3) / Starlette (1.2.1), `StreamingResponse` no longer cancels the response body iterator on `http.disconnect` (ASGI spec 2.4+), so the server now detects the disconnect itself by polling `request.is_disconnected()` while streaming and interrupts the kernel.
