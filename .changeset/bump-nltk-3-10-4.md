---
'@e2b/code-interpreter-template': patch
---

Bump `nltk` to 3.10.4 (GHSA-8mgp-746c-j5xp). NLTK now confines resource reads/writes to `nltk.data.path`, loads pickled models through a restricted unpickler and skips world-writable data directories (e.g. under `/tmp`); the default `~/nltk_data` is unaffected.
