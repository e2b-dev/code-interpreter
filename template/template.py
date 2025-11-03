from e2b import Template, wait_for_port, wait_for_url


def make_template(
    kernels: list[str] = ["python", "r", "javascript", "deno", "bash", "java"],
    set_user_workdir: bool = False,
):
    # Start with base template
    template = (
        Template()
        .from_image("python:3.12")
        .set_user("root")
        .set_workdir("/")
        .set_envs(
            {
                "PIP_DEFAULT_TIMEOUT": "100",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1",
                "JUPYTER_CONFIG_PATH": ".jupyter",
                "IPYTHON_CONFIG_PATH": ".ipython",
                "SERVER_PATH": ".server",
                "R_VERSION": "4.4.2",
                "R_HOME": "/opt/R/4.4.2",
                "JAVA_HOME": "/opt/java/openjdk",
                "DENO_INSTALL": "/opt/deno",
            }
        )
        .apt_install(
            [
                "build-essential",
                "curl",
                "git",
                "util-linux",
                "jq",
                "sudo",
                "fonts-noto-cjk",
            ]
        )
        .run_cmd("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
        .apt_install("nodejs")
        .copy("requirements.txt", "requirements.txt")
        .pip_install("--no-cache-dir -r requirements.txt")
    )

    if "python" in kernels:
        template = template.run_cmd("ipython kernel install --name 'python3' --user")

    # Install R Kernel if requested
    if "r" in kernels:
        template = (
            template.apt_install("r-base")
            .run_cmd(
                [
                    "R -e \"install.packages('IRkernel', repos='https://cloud.r-project.org')\"",
                    "R -e \"IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')\"",
                ]
            )
        )

    # Install JavaScript Kernel if requested
    if "javascript" in kernels:
        template = template.npm_install(
            "--unsafe-perm git+https://github.com/e2b-dev/ijavascript.git",
            g=True,
        ).run_cmd("ijsinstall --install=global")

    # Install Deno Kernel if requested
    if "deno" in kernels:
        template = template.run_cmd(
            [
                "curl -fsSL https://deno.land/x/install/install.sh | sh",
                "PATH=/opt/deno/bin:$PATH",
                "deno jupyter --unstable --install",
            ]
        )
        template = template.copy(
            "deno.json", ".local/share/jupyter/kernels/deno/kernel.json"
        )

    # Install Bash Kernel if requested
    if "bash" in kernels:
        template = template.pip_install("bash_kernel").run_cmd(
            "python -m bash_kernel.install"
        )

    # Install Java and Java Kernel if requested
    if "java" in kernels:
        template = template.apt_install("default-jdk")
        template = template.run_cmd(
            [
                "wget https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip",
                "unzip ijava-1.3.0.zip",
                "python install.py --sys-prefix",
            ]
        )

    # Common setup steps (always run)
    template = (
        template
        # Create server virtual environment
        .copy("server", ".server")
        .run_cmd("python -m venv .server/.venv")
        # Copy and install server requirements
        .run_cmd(
            ".server/.venv/bin/pip install --no-cache-dir -r .server/requirements.txt"
        )
    )

    if set_user_workdir:
        template = template.set_user("user").set_workdir("/home/user")

    # Copy configuration files
    template = (
        template.copy("matplotlibrc", ".config/matplotlib/.matplotlibrc")
        .copy("start-up.sh", ".jupyter/start-up.sh")
        .run_cmd("chmod +x .jupyter/start-up.sh")
        .copy("jupyter_server_config.py", ".jupyter/")
        .make_dir(".ipython/profile_default/startup")
        .copy("ipython_kernel_config.py", ".ipython/profile_default/")
        .copy("startup_scripts", ".ipython/profile_default/startup")
    )

    return template.set_start_cmd(".jupyter/start-up.sh", wait_for_url("http://localhost:49999/health"))
