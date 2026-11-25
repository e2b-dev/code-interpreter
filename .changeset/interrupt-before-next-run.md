---
'@e2b/code-interpreter-template': patch
---

Fix the next execution timing out after a client abandons a long-running one: the server now waits for the interrupted execution to end before sending the next code to the kernel, and ends executions the kernel aborts instead of waiting for them forever.
