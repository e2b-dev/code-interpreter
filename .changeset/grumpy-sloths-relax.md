---
'@e2b/code-interpreter': patch
'@e2b/code-interpreter-python': patch
---

Throw a descriptive `TimeoutError`/`TimeoutException` instead of a raw socket error (e.g. `ECONNRESET`) when the sandbox is killed or times out while a request (`runCode`/`run_code`, context management) is in progress
