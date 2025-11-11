from e2b import Template, wait_for_url


def make_template(
    kernels: list[str] = ["python", "r", "javascript", "deno", "bash", "java"],
    is_docker: bool = False,
):
    enabled_kernels = set(["python", "javascript"] + kernels)
    # Start with base template
    template = (
        Template()
        .from_image("python:3.12")
        .set_user("root")
        .set_workdir("/root")
        .set_envs(
            {
                "PIP_DEFAULT_TIMEOUT": "100",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1",
                "JUPYTER_CONFIG_PATH": "/root/.jupyter",
                "IPYTHON_CONFIG_PATH": "/root/.ipython",
                "SERVER_PATH": "/root/.server",
                "JAVA_VERSION": "11",
                "JAVA_HOME": "/usr/lib/jvm/jdk-${JAVA_VERSION}",
                "IJAVA_VERSION": "1.3.0",
                "DENO_INSTALL": "/opt/deno",
                "DENO_VERSION": "v2.4.0",
                "R_VERSION": "4.5.*",
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
        .copy("requirements.txt", "requirements.txt")
        .pip_install("--no-cache-dir -r requirements.txt")
    )

    if "python" in enabled_kernels:
        template = template.run_cmd("ipython kernel install --name 'python3' --user")

    # Install R Kernel if requested
    if "r" in enabled_kernels:
        template = (
            template.run_cmd(
                [
                    "sudo gpg --keyserver keyserver.ubuntu.com --recv-key 95C0FAF38DB3CCAD0C080A7BDC78B2DDEABC47B7",
                    "sudo gpg --armor --export 95C0FAF38DB3CCAD0C080A7BDC78B2DDEABC47B7 | sudo tee /etc/apt/trusted.gpg.d/cran_debian_key.asc",
                    'echo "deb https://cloud.r-project.org/bin/linux/debian trixie-cran40/" | sudo tee /etc/apt/sources.list.d/cran.list',
                ]
            )
            .apt_install("r-base=${R_VERSION} r-base-dev")
            .run_cmd(
                [
                    "R -e \"install.packages('IRkernel', repos='https://cloud.r-project.org')\"",
                    "R -e \"IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')\"",
                ]
            )
        )

    # Install JavaScript Kernel if requested
    if "javascript" in enabled_kernels:
        template = template.npm_install(
            "--unsafe-perm git+https://github.com/e2b-dev/ijavascript.git",
            g=True,
        ).run_cmd("ijsinstall --install=global")

    # Install Deno Kernel if requested
    if "deno" in enabled_kernels:
        template = template.run_cmd(
            [
                "curl -fsSL https://deno.land/install.sh | sh -s ${DENO_VERSION}",
                "PATH=$DENO_INSTALL/bin:$PATH",
                "deno jupyter --unstable --install",
            ]
        ).copy("deno.json", ".local/share/jupyter/kernels/deno/kernel.json")

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
        template
        .copy("matplotlibrc", ".config/matplotlib/.matplotlibrc")
        .copy("start-up.sh", ".jupyter/start-up.sh")
        .run_cmd("chmod +x .jupyter/start-up.sh")
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
        template = template.run_cmd("echo 'user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers")
        # own everything in /root to user
        template = template.run_cmd("chown -R user:user /root")

    template = template.set_user("user").set_workdir("/home/user")

    return template.set_start_cmd(
        "sudo /root/.jupyter/start-up.sh", wait_for_url("http://localhost:49999/health")
    )
