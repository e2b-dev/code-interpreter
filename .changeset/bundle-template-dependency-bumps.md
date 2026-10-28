---
'@e2b/code-interpreter-template': patch
---

Bump template Python packages: `jupyter-server==2.21.1` (GHSA-c3mw-737p-c7g2), `matplotlib==3.11.2`, `pillow==13.0.0`, `aiohttp==3.14.5`, `tornado==6.6` and `urllib3==2.8.0`.

matplotlib 3.11 removes APIs deprecated in 3.9, e.g. `Axes.boxplot(labels=...)` is now `tick_labels=...`.
