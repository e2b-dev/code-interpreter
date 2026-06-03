---
"@e2b/code-interpreter-template": patch
---

Improve template debuggability: send Jupyter's stdout to the systemd journal (instead of /dev/null) so startup errors are visible, and add a `make debug-template` workflow that builds via the systemd path and dumps the service journals for diagnosing a server that fails to start.
