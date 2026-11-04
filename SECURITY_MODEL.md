# Security model: Code Interpreter template

This file describes what this repository is trusted to do, who might attack it, and which risks are accepted. Security scans read it to prioritize findings. It is one of four views of the same system:

- [e2b-dev/E2B](https://github.com/e2b-dev/E2B/blob/main/SECURITY_MODEL.md): SDKs and CLI
- [e2b-dev/code-interpreter](https://github.com/e2b-dev/code-interpreter/blob/main/SECURITY_MODEL.md): code interpreter template
- [e2b-dev/desktop](https://github.com/e2b-dev/desktop/blob/main/SECURITY_MODEL.md): desktop template
- [e2b-dev/customer-starter-templates](https://github.com/e2b-dev/customer-starter-templates/blob/main/SECURITY_MODEL.md): customer starter templates

The E2B API, edge proxy, envd server and sandbox isolation (Firecracker) live in other repositories and are not covered here.

## System overview

Developers' code (often an AI agent) uses the E2B SDKs and CLI on a **host** (laptop, server, CI) to create sandboxes on E2B clusters and to run code, files and processes in them. Templates define what runs inside a sandbox.

Trust boundaries:

1. **Host to E2B API** (`api.<E2B_DOMAIN>`): HTTPS with `X-API-Key` (team API key) or `Authorization: Bearer` (access token).
2. **Host to sandbox envd** (`<port>-<sandboxId>.<E2B_DOMAIN>`): Connect RPC/HTTP with `X-Access-Token` (envd access token), a Basic auth username for the run-as user, signed file URLs, and `e2b-traffic-access-token` for public ports.
3. **Sandbox to host**: everything a sandbox returns (command output, files, paths, Jupyter results, VNC, MCP responses) is produced by untrusted code.
4. **Internet to sandbox ports**: ports are reachable through the E2B edge by hostname unless the sandbox requires a traffic access token.
5. **GitHub PRs and supply chain to CI**: workflows build templates and publish packages, images and templates.

## Components

| Component | Code |
|---|---|
| **code-interpreter-template** | `template/`: FastAPI server (`template/server`) on `0.0.0.0:49999` that talks to Jupyter over a UNIX socket, startup scripts (`template/start-up.sh`, `template/systemd`), `chart_data_extractor/` |
| **ci-release** | `.github/workflows/*`: template builds, tests, releases |

The SDKs that call this server are **addon-sdks** (`packages/code-interpreter-{js,python}` in e2b-dev/E2B).

## Entry points

- Code interpreter server on port 49999 (`/execute`, `/contexts`, restart, delete). It does not check `X-Access-Token` and allows every CORS origin; it is reachable through the E2B edge when the sandbox allows public traffic.
- Jupyter server started with `--IdentityProvider.token=""`.
- Env vars and context `cwd` from the SDK, which the server places into kernel code (`template/server/messaging.py`).
- Results, charts and errors returned to the SDK (boundary 3).
- CI: `pull_request.yml` runs PR code with `E2B_API_KEY` and `id-token: write`; `release.yml` uses OIDC, `DOCKERHUB_TOKEN` and `E2B_PROD_API_KEY`. No workflow uses `pull_request_target`.

## Existing controls

- The server talks to Jupyter over a UNIX socket with `trust_env=False`.
- Requests from the internet are expected to be blocked by the edge unless the sandbox allows public traffic or the caller has the traffic access token.

## Accepted risk

- **In-sandbox services without authentication are by design** (code interpreter server and Jupyter with an empty token, x11vnc/noVNC without a password, the MCP gateway without a token, other template daemons). Code running in the sandbox already owns the sandbox. A finding whose only impact is that a process inside the sandbox can reach such a service is accepted risk.
- Still in scope: reaching those services **from the internet** without the owner's tokens, and SDK bugs that turn off authentication the user asked for (`requireAuth`, `secure`, traffic access tokens).
- Server-side components and sandbox isolation are out of scope here.

## Attackers

All of these matter equally:

1. **Untrusted code inside the sandbox** (LLM-generated or user-supplied) attacking the host through what it returns: file names and paths, symlinks, oversized or malformed responses, terminal escape sequences, poisoned results.
2. **Internet users reaching sandbox ports** without the owner's tokens.
3. **Malicious PR authors and supply-chain attackers** against CI, release pipelines, template build scripts and third-party downloads.
4. **Network attackers** between the host and E2B (TLS, custom CA, `E2B_DOMAIN` overrides).
5. **Local attackers and malicious web pages** on the developer's machine.

## Assets

All equally important: users' E2B API keys and access/refresh tokens; envd and traffic access tokens and signed file URLs; CI and publishing credentials (npm/PyPI trusted publishing, Docker Hub, GitHub App keys, per-cluster E2B keys); customer data in sandboxes (files, env vars, secrets, desktop sessions); integrity of the host running the SDK or CLI.

## Finding tags

- `CWE`: CWE id of the weakness, e.g. `CWE-22`.
- `CVE`: CVE id for dependency findings.
- `package`: affected package or template (`js-sdk`, `python-sdk`, `cli`, `code-interpreter-sdk`, `desktop-sdk`, `dockerfile-utils`, `code-interpreter-template`, `desktop-template`, `template:<name>`, `ci`).

## Open questions

- What is the server-side default for `allowPublicTraffic`, and how often are sandbox ids exposed (for example in shared preview hostnames)?
