---
'@e2b/code-interpreter': patch
'@e2b/code-interpreter-python': patch
---

Point the README documentation links at `docs.e2b.dev` instead of `e2b.dev/docs`. The docs site moved to its own subdomain and the old path has no `/docs` prefix there, so `e2b.dev/docs` now serves a 308 to `docs.e2b.dev/`. The UTM parameters are unchanged and survived the redirect, so this removes a redirect hop rather than fixing broken attribution.
