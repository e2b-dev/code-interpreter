# Code Interpreter template

This template runs a Jupyter server with a Python kernel. The jupyter server is started in `start_cmd`, this way the server will be already running when the sandbox is started.

## Customization

If you want to add another packages, another kernels or simply change some configuration and still use CodeInterpreter SDK, you will need to follow these steps:

1. Copy `jupyter_server_config.py`, `ipython_kernel_config.py` and `start-up.sh` from [this folder](./).
2. Add following commands in your Dockerfile

```Dockerfile
# Installs jupyter server and kernel
RUN pip install jupyter-server ipykernel ipython
RUN ipython kernel install --name "python3" --user

# Copies jupyter server config
COPY ./jupyter_server_config.py /home/user/.jupyter/

# Setups jupyter server
COPY ./start-up.sh /home/user/.jupyter/
RUN chmod +x /home/user/.jupyter/start-up.sh
```

3. Add the following option `-c "/home/user/.jupyter/start-up.sh"` to `e2b template build` command or add this line to your `e2b.toml`.

```yaml
start_cmd = "/home/user/.jupyter/start-up.sh"
```  

## Use E2B code interpreter image

Alternatively you can use prebuilt E2B Code Interpreter image. You can find it on Docker Hub: [e2b/code-interpreter](https://hub.docker.com/r/e2bdev/code-interpreter). You can simply write

```Dockerfile
FROM e2bdev/code-interpreter:latest
```

instead of the step `1` and `2` above. You still HAVE TO add the `start_cmd` option to your `e2b.toml` or `e2b template build` command.
