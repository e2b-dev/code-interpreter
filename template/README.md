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

## Process supervision

Jupyter and the code-interpreter server are supervised by
[process-compose](https://f1bonacc1.github.io/process-compose/), configured in
`process-compose.yaml`. The same config runs in the E2B sandbox and in the
Docker image (`make start-template-server`), so a server that boots under
Docker boots the same way in production.

The two servers are not independent: the code-interpreter server opens kernel
websockets while starting, so it is gated on Jupyter being up
(`jupyter-healthcheck.sh`) and is restarted whenever Jupyter is replaced
(`jupyter-instance-check.sh`, which compares Jupyter's reported start time
against the one recorded at gate time).

Jupyter writes to its log file directly rather than through process-compose,
because kernels inherit its stdout and stderr and outlive it — with
process-compose holding those descriptors, a killed Jupyter is not restarted
while any kernel is still running. The cost is that `process-compose process
logs jupyter` shows nothing and the file is not rotated; read
`/var/log/jupyter.log` instead.

## Debugging a server that won't start

When a build fails its readiness check (`Waiting for template to be ready ...
timed out`), the cause is in the process logs. To see them:

```
make debug-template
```

This builds a debug template (gated on a fixed timeout instead of `/health`, so
it finalizes even while the server is crash-looping), spawns a sandbox, and
prints the process list and all three logs. It needs `template/.env` with your
`E2B_API_KEY` and the deps from `requirements-dev.txt`.

Inside a running sandbox you can inspect things directly:

```
cat /var/log/process-compose.log   # restarts, probe failures
cat /var/log/jupyter.log
cat /var/log/code-interpreter.log

# process-compose listens on a unix socket rather than a TCP port, so its
# subcommands need to be pointed at it
alias pc='process-compose -U -u /var/run/process-compose.sock'
pc process list
pc process restart code-interpreter
```
