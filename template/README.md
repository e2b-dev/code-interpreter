# Using custom sandbox with Code Interpreter SDK

If you want to customize the Code Interpreter sandbox (e.g.: add a preinstalled package) you can do that by creating a [custom sandbox template](https://e2b.dev/docs/template/quickstart).

## Step-by-step guide

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

3. Build the template:

```
python build.py
```

4. Use the custom template:

```python
from e2b import Sandbox

sbx = Sandbox.create(template="code-interpreter-custom")
execution = sbx.run_code("print('Hello, World!')")
print(execution.logs.stdout)
```
