# E2B Template SDK (Python)

## Quick Start

Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install required dependencies

```bash
pip install httpx openapi-python-client dotenv e2b
```

Install E2B Template SDK from **Test PyPI**

```bash
pip install -i https://test.pypi.org/simple/ e2b-template
```

Create the `.env` file

```
E2B_API_KEY=

#If custom domain is used, uncomment and set
#E2B_DOMAIN=
```

Create a new file named `template.py` with the following content:

**template.py**

```python
from e2b_template import Template, wait_for_timeout

template = (
    Template()
    .from_image("ubuntu:22.04")
    .set_envs(
        {
            "HELLO": "Hello, World!",
        }
    )
    .set_start_cmd("echo $HELLO", wait_for_timeout("5s"))
)
```

Create a new development build script `build_dev.py`:

**build_dev.py**

```python
from dotenv import load_dotenv
from e2b_template import Template
from template import template

load_dotenv()

Template.build(
    template,
    alias="template-tag-dev",
    cpu_count=1,
    memory_mb=1024,
    on_build_logs=lambda log_entry: print(log_entry),
)
```

Build the development template

```bash
python build_dev.py
```

Create a new production build script `build_prod.py`:

**build_prod.py**

```python
from dotenv import load_dotenv
from e2b_template import Template
from template import template

load_dotenv()

Template.build(
    template,
    alias="template-tag",
    cpu_count=1,
    memory_mb=1024,
    on_build_logs=lambda log_entry: print(log_entry),
)
```

Build the production template

```bash
python build_prod.py
```

Create a new Sandbox from template

**main.py**

```python
from dotenv import load_dotenv
from e2b_template import Template
from template import template

load_dotenv()

# Create a new Sandbox from the development template
sbx = Sandbox(template="template-tag-dev")

# Create a new Sandbox from the production template
sbx = Sandbox(template="template-tag")
```

## Examples

Examples are available in the [examples](./examples) directory.

## Usage

### Authentication

The SDK uses environment variables for authentication:

- `E2B_API_KEY`: Your E2B API key
- `E2B_DOMAIN`: (Optional) E2B domain, defaults to 'e2b.dev'

### Creating templates

When creating a template, you can specify options:

```python
template = Template(
    file_context_path=".",  # Custom file context path
    ignore_file_paths=[".git", "node_modules"],  # File patterns to ignore
)
```

**File ignoring**: The SDK automatically reads `.dockerignore` files and combines them with your `ignore_file_paths`. Files matching these patterns are excluded from uploads and hash calculations.

### Method chaining

All template methods return the template instance, allowing for fluent API usage:

```python
template = (
    Template()
    .from_ubuntu_image("22.04")
    .set_workdir("/app")
    .copy("package.json", "/app/package.json")
    .run_cmd("npm install")
    .set_start_cmd("npm start", wait_for_timeout("10s"))
)
```

### Base images

Choose from predefined base images or use custom ones:

```python
# Predefined base images
template.from_ubuntu_image("lts")  # ubuntu:lts
template.from_ubuntu_image("22.04")  # ubuntu:22.04
template.from_debian_image("slim")  # debian:slim
template.from_debian_image("bullseye")  # debian:bullseye
template.from_python_image("3.13")  # python:3.13
template.from_python_image("3.11")  # python:3.11
template.from_node_image("lts")  # node:lts
template.from_node_image("20")  # node:20

# Custom base image
template.from_image("custom-image:latest")

# Use default E2B base image
template.from_base_image()  # e2bdev/base

# Build from existing template
template.from_template("existing-template-alias")

# Parse and build from Dockerfile
template.from_dockerfile("Dockerfile")
template.from_dockerfile("FROM ubuntu:22.04\nRUN apt-get update")
```

**Note**: You can only call `from_image()`, `from_template()`, or `from_dockerfile()` once per template. Subsequent calls will throw an error.

### User and workdir

Set the working directory and user for the template:

```python
# Set working directory
template.set_workdir("/app")

# Set user (runs subsequent commands as this user)
template.set_user("node")
template.set_user("1000:1000")  # User ID and group ID
```

### Copying files

Copy files from your local filesystem to the template:

```python
# Copy a single file
template.copy("package.json", "/app/package.json")

# Copy multiple files
template.copy([
    {"src": "src/", "dest": "/app/src/"},
    {"src": "package.json", "dest": "/app/package.json"},
])

# Force upload (bypass cache)
template.copy("config.json", "/app/config.json", force_upload=True)
```

### File and directory operations

Manage files and directories in the template:

```python
# Remove files or directories
template.remove("/tmp/old-file")
template.remove("/tmp/old-dir", recursive=True)
template.remove("/tmp/file", force=True)  # Force removal

# Rename files or directories
template.rename("/old/path", "/new/path")
template.rename("/old/path", "/new/path", force=True)  # Force rename

# Create directories
template.make_dir("/app/data")
template.make_dir("/app/data", mode=0o755)  # Set permissions

# Create symbolic links
template.make_symlink("/path/to/target", "/path/to/link")
```

### Installing packages

Install packages using package managers:

```python
# Install Python packages
template.pip_install("requests pandas numpy")
template.pip_install(["requests", "pandas", "numpy"])

# Install Node.js packages
template.npm_install("express lodash")
template.npm_install(["express", "lodash"])

# Install system packages (Ubuntu/Debian)
template.apt_install("curl wget git")
template.apt_install(["curl", "wget", "git"])
```

### Git operations

Clone git repositories into the template (requires `git` to be installed):

```python
# Basic clone
template.git_clone("https://github.com/user/repo.git", "/app/repo")

# Clone specific branch
template.git_clone("https://github.com/user/repo.git", "/app/repo", branch="main")

# Shallow clone with depth limit
template.git_clone("https://github.com/user/repo.git", "/app/repo", depth=1)
```

### Environment variables

Set environment variables in the template:

```python
template.set_envs({
    "NODE_ENV": "production",
    "API_KEY": "your-api-key",
    "DEBUG": "true",
})
```

### Invalidating caches

Force rebuild from the next instruction:

```python
template.skip_cache()
```

This will invalidate the cache for all subsequent instructions in the template.

### Running commands

Execute shell commands during template build:

```python
# Run a single command
template.run_cmd("apt-get update && apt-get install -y curl")

# Run multiple commands
template.run_cmd(["apt-get update", "apt-get install -y curl", "curl --version"])

# Run command as specific user
template.run_cmd("npm install", user="node")
```

### Configuring start command and ready command

Set the command that runs when the sandbox starts and the command that determines when the sandbox is ready:

```python
# Set both start command and ready command
template.set_start_cmd("npm start", wait_for_timeout("10s"))

# Set only ready command (after setting start command)
template.set_ready_cmd(wait_for_port(3000))
# Note: you need to have installed curl in order to use the wait_for_port helper
```

The ready command is used to determine when the sandbox is ready to accept connections.

**Note**: You can only call `set_start_cmd()` and `set_ready_cmd()` once per template. Subsequent calls will throw an error.

### Ready command helpers

The SDK provides helper functions to generate common ready commands:

```python
from e2b_template import wait_for_port, wait_for_process, wait_for_file, wait_for_timeout

# Wait for a port to be available, curl needs to be installed
wait_for_port(3000)

# Wait for a process to be running
wait_for_process("nginx")

# Wait for a file to exist
wait_for_file("/tmp/ready")

# Wait for a specified duration
wait_for_timeout("30s")
```

### Build options

Configure the build process:

```python
Template.build(
    template,
    alias="my-template",  # Template alias (required)
    cpu_count=2,  # CPU cores
    memory_mb=2048,  # Memory in MB
    skip_cache=True,  # Skip all caching (except for files)
    on_build_logs=lambda log_entry: print(log_entry),  # Log callback receives LogEntry objects
    api_key="your-api-key",  # Override API key
    domain="your-domain",  # Override domain
)
```

#### Build logging

The `on_build_logs` callback receives structured `LogEntry` objects with the following properties:

```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: Literal["debug", "info", "warn", "error"]
    message: str

    def __str__(self) -> str:  # Returns formatted log string
```

You can customize how logs are handled:

```python
# Simple logging
on_build_logs=lambda log_entry: print(log_entry)

# Custom formatting
def custom_logger(log_entry):
    time = log_entry.timestamp.isoformat()
    print(f"[{time}] {log_entry.level.upper()}: {log_entry.message}")

Template.build(template, alias="my-template", on_build_logs=custom_logger)

# Filter by log level
def error_logger(log_entry):
    if log_entry.level in ["error", "warn"]:
        print(f"ERROR/WARNING: {log_entry}", file=sys.stderr)

Template.build(template, alias="my-template", on_build_logs=error_logger)
```

### Error handling

The SDK provides specific error types:

```python
from e2b_template.errors import AuthError, BuildError, FileUploadError

try:
    Template.build(template, alias="my-template", cpu_count=1, memory_mb=1024)
except AuthError as error:
    print(f"Authentication failed: {error}")
except FileUploadError as error:
    print(f"File upload failed: {error}")
except BuildError as error:
    print(f"Build failed: {error}")
```