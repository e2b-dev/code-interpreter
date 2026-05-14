---
'@e2b/code-interpreter-template': patch
---

Apply cwd to bash kernel contexts (previously ignored, so `pwd` returned `/` regardless of the requested working directory)
