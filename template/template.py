from e2b import ReadyCmd, Template, wait_for_url


def make_template(
    kernels: list[str] = ["python", "r", "javascript", "bash", "java"],
    is_docker: bool = False,
    ready: ReadyCmd | None = None,
):
    enabled_kernels = set(["python", "javascript"] + kernels)
    # Start with base template
    template = (
        Template()
        .from_image("python:3.13")
        .set_user("root")
        .set_workdir("/root")
        .set_envs(
            {
                "PIP_DEFAULT_TIMEOUT": "100",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1",
                "JAVA_VERSION": "11",
                "JAVA_HOME": "/usr/lib/jvm/jdk-${JAVA_VERSION}",
                "IJAVA_VERSION": "1.3.0",
                "R_VERSION": "4.5.*",
                "PROCESS_COMPOSE_VERSION": "1.120.0",
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
                "ca-certificates",
            ]
        )
        .run_cmd("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
        .apt_install("nodejs")
        # Supervises Jupyter and the Code Interpreter server; see
        # process-compose.yaml. Built for the image's own architecture so the
        # Docker path works on arm64 machines too.
        .run_cmd(
            "curl -fsSL https://github.com/F1bonacc1/process-compose/releases/download"
            "/v${PROCESS_COMPOSE_VERSION}/process-compose_linux_$(dpkg --print-architecture).tar.gz"
            " | tar -xz -C /usr/local/bin process-compose"
        )
        .copy("requirements.txt", "requirements.txt")
        .pip_install("--no-cache-dir -r requirements.txt")
    )

    if "python" in enabled_kernels:
        template = template.run_cmd("ipython kernel install --name 'python3' --user")

    # Install R Kernel if requested
    if "r" in enabled_kernels:
        template = template.apt_install("r-base=${R_VERSION} r-base-dev").run_cmd(
            [
                "R -e \"install.packages('IRkernel', repos='https://cloud.r-project.org')\"",
                "R -e \"IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')\"",
            ]
        )

    # Install JavaScript Kernel if requested
    if "javascript" in enabled_kernels:
        template = template.npm_install(
            "--unsafe-perm git+https://github.com/e2b-dev/ijavascript.git",
            g=True,
        ).run_cmd("ijsinstall --install=global")

    # Install Bash Kernel if requested
    if "bash" in enabled_kernels:
        template = template.pip_install("bash_kernel").run_cmd(
            "python -m bash_kernel.install"
        )

    # Install Java and Java Kernel if requested
    if "java" in enabled_kernels:
        template = template.run_cmd(
            [
                "mkdir -p /usr/lib/jvm",
                "curl -fsSL https://download.java.net/java/ga/jdk${JAVA_VERSION}/openjdk-${JAVA_VERSION}_linux-x64_bin.tar.gz | tar -xz -C /usr/lib/jvm",
                "update-alternatives --install /usr/bin/java java /usr/lib/jvm/jdk-${JAVA_VERSION}/bin/java 1",
                "update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/jdk-${JAVA_VERSION}/bin/javac 1",
                "wget https://github.com/SpencerPark/IJava/releases/download/v${IJAVA_VERSION}/ijava-${IJAVA_VERSION}.zip",
                "unzip ijava-${IJAVA_VERSION}.zip",
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

    # Copy configuration files
    template = (
        template.copy("matplotlibrc", ".config/matplotlib/.matplotlibrc")
        .copy("jupyter-healthcheck.sh", ".jupyter/jupyter-healthcheck.sh")
        .copy("jupyter-instance-check.sh", ".jupyter/jupyter-instance-check.sh")
        .run_cmd(
            "chmod +x .jupyter/jupyter-healthcheck.sh .jupyter/jupyter-instance-check.sh"
        )
        .copy("process-compose.yaml", ".jupyter/process-compose.yaml")
        .copy("jupyter_server_config.py", ".jupyter/")
        .make_dir(".ipython/profile_default/startup")
        .copy("ipython_kernel_config.py", ".ipython/profile_default/")
        .copy("startup_scripts", ".ipython/profile_default/startup")
    )

    if is_docker:
        # create user user and /home/user
        template = template.run_cmd("useradd -m user")
        template = template.run_cmd("mkdir -p /home/user")
        template = template.run_cmd("chown -R user:user /home/user")
        # add to sudoers
        template = template.run_cmd(
            "echo 'user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"
        )

    template = template.set_user("user").set_workdir("/home/user")

    # --disable-dotenv keeps a stray .env in the working directory out of the
    # servers' environment, and the unix socket keeps process-compose's control
    # API off a TCP port the sandbox would otherwise expose.
    start_cmd = (
        "sudo --preserve-env=E2B_LOCAL process-compose up"
        " --config /root/.jupyter/process-compose.yaml"
        " --log-file /var/log/process-compose.log"
        " --unix-socket /var/run/process-compose.sock"
        " --use-uds --disable-dotenv --ordered-shutdown --tui=false"
    )

    if ready is None:
        ready = wait_for_url("http://localhost:49999/health")

    return template.set_start_cmd(start_cmd, ready)
