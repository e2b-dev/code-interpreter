# Code Interpreter

## Building the production template

To build the official `code-interpreter-v1` template from this repo, use
`build_prod.py`. This is the script CI and releases run.

1. Install the build dependencies:

```
pip install -r requirements-dev.txt
```

2. Provide your credentials in `.env`:

```
E2B_API_KEY=e2b_***
```

3. Build the template:

```
python build_prod.py
```

Set `SKIP_CACHE=true` to force a clean rebuild that ignores the layer cache:

```
SKIP_CACHE=true python build_prod.py
```

If you want to customize the Code Interpreter sandbox (e.g.: add a preinstalled package) you can do that by creating a [custom sandbox template](https://e2b.dev/docs/template/quickstart).

## Creating a custom template

1. Install E2B SDK

```
pip install e2b dotenv
```

2. Create a custom sandbox template:

**template.py**

```python
from e2b import Template

template = Template().from_template("code-interpreter-v1")
```

3. Create a build script:

**build.py**

```python
from dotenv import load_dotenv
from .template import template
from e2b import Template, default_build_logger

load_dotenv()

Template.build(
    template,
    alias="code-interpreter-custom",
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)
```

4. Set your environment variables in a `.env` file (loaded by `load_dotenv()`):

```
E2B_API_KEY=e2b_***
```

5. Build the template:

```
python build.py
```

6. Use the custom template:

```python
from e2b import Sandbox

sbx = Sandbox.create(template="code-interpreter-custom")
execution = sbx.run_code("print('Hello, World!')")
print(execution.logs.stdout)
```

## Debugging a server that won't start

The template runs Jupyter and the code-interpreter server as **systemd**
services (`systemd/jupyter.service`, `systemd/code-interpreter.service`). This is
the path CI and production use — note it is *different* from `make
start-template-server`, which runs the Docker `start-up.sh` path. The two can
diverge, so a server that boots fine under Docker may still fail under systemd.

When a build fails its readiness check (`Waiting for template to be ready ...
timed out`), the real cause is in the service journals. To see them:

```
make debug-template
```

This builds a debug template (gated on a fixed timeout instead of `/health`, so
it finalizes even while the server is crash-looping), spawns a sandbox, and
prints `systemctl status` + the full `journalctl` for both services. It needs
`template/.env` with your `E2B_API_KEY` and the deps from `requirements-dev.txt`.

The debug build also applies a systemd drop-in that routes Jupyter's stdout to
the journal (`make_template(debug=True)`). Production builds keep
`StandardOutput=null`, so Jupyter's request/error logs are only captured in the
debug template.

Inside a running sandbox you can also inspect things directly:

```
journalctl -u jupyter -u code-interpreter
systemctl status code-interpreter
```

## Interpreter authentication

The template requires envd 0.9.1 or later with the local token delivery socket.
The server receives a SHA-512 token verifier over `/run/e2b-auth/token.sock` and
validates `X-Access-Token` locally. It rejects requests before provisioning and
after disconnecting. `/health` needs no bearer token, but remains unavailable
until the auth connection is established. Tokenless sandboxes cannot execute code.

The systemd service creates `/etc/e2b/code-interpreter-auth` when first started.
This marker contains no credentials; it makes envd wait for token delivery to be
acknowledged during initialization, including resume and fork. The auth connection
is also reestablished after an interpreter or envd restart.

Deploy envd and SDK context-auth updates before rebuilding this template. Local
Docker development explicitly sets `E2B_LOCAL=true`, which disables auth; do not
use that setting in deployed templates. Authentication protects the interpreter
API on port `49999`; it does not change Jupyter's listener or secure direct
access to Jupyter. Jupyter isolation is a separate transport change.

Run the authentication tests locally with:

```sh
uv run --with-requirements template/requirements-test.txt pytest template/tests/test_auth.py
```
