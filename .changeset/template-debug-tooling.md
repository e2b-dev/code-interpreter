---
"@e2b/code-interpreter-template": patch
---

Add a `make debug-template` workflow for diagnosing a server that fails to start: it builds the template via the systemd path (with a fixed-timeout ready gate and a drop-in routing Jupyter's stdout to the journal) and dumps the service journals. Production builds are unchanged.
