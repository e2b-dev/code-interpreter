from e2b_template import Template, wait_for_port


def make_template(
    kernels: list[str] = ["python", "r", "javascript", "deno", "bash", "java"],
):
    # Start with base template
    template = (
        Template()
        .from_image("python:3.12")
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
                "DENO_INSTALL": "$HOME/.deno",
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
            template.run_cmd(
                "curl -O https://cdn.rstudio.com/r/debian-12/pkgs/r-4.4.2_1_amd64.deb"
            )
            .apt_install("./r-4.4.2_1_amd64.deb")
            .run_cmd("ln -s /opt/R/4.4.2/bin/R /usr/bin/R")
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
            "-g --unsafe-perm git+https://github.com/e2b-dev/ijavascript.git"
        ).run_cmd("ijsinstall --install=global")

    # Install Deno Kernel if requested
    if "deno" in kernels:
        template = template.run_cmd(
            [
                "curl -fsSL https://deno.land/x/install/install.sh | sh",
                "PATH=$HOME/.deno/bin:$PATH",
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
        .run_cmd(
            [
                "python -m venv .server/.venv",
                ". .server/.venv/bin/activate",
            ]
        )
        # Copy and install server requirements
        .run_cmd(
            ".server/.venv/bin/pip install --no-cache-dir -r .server/requirements.txt"
        )
        # Copy configuration files
        .copy("matplotlibrc", ".config/matplotlib/.matplotlibrc")
        .copy("start-up.sh", ".jupyter/start-up.sh", mode=0o755, user="root")
        # .run_cmd("chmod +x .jupyter/start-up.sh")
        .copy("jupyter_server_config.py", ".jupyter/")
        .run_cmd("mkdir -p .ipython/profile_default/startup")
        .copy("ipython_kernel_config.py", ".ipython/profile_default/")
        .copy("startup_scripts", ".ipython/profile_default/startup")
        .set_start_cmd(".jupyter/start-up.sh", wait_for_port(49999))
    )

    return template
