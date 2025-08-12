from e2b_template import Template, wait_for_port

def make_template(kernels: list[str] = ["python", "r", "javascript", "deno", "bash", "java"]):
    # Start with base template
    template = (
        Template()
        .from_image("python:3.12")
        .run_cmd([
            "DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends build-essential curl git util-linux jq sudo fonts-noto-cjk",
            "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
            "apt-get install -y nodejs"
        ])
        .set_envs({
            "PIP_DEFAULT_TIMEOUT": "100",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_CACHE_DIR": "1",
            "JUPYTER_CONFIG_PATH": "/root/.jupyter",
            "IPYTHON_CONFIG_PATH": "/root/.ipython",
            "SERVER_PATH": "/root/.server",
            "R_VERSION": "4.4.2",
            "R_HOME": "/opt/R/4.4.2",
            "JAVA_HOME": "/opt/java/openjdk"
        })
        .copy("requirements.txt", "/root/requirements.txt")
        .run_cmd([
            "pip install --no-cache-dir -r /root/requirements.txt",
            "ipython kernel install --name 'python3' --user"
        ])
    )
    
    # Install R Kernel if requested
    if "r" in kernels:
        template = template.run_cmd([
            "curl -O https://cdn.rstudio.com/r/debian-12/pkgs/r-4.4.2_1_amd64.deb",
            "sudo apt-get update",
            "sudo apt-get install -y ./r-4.4.2_1_amd64.deb",
            "ln -s /opt/R/4.4.2/bin/R /usr/bin/R",
            "R -e \"install.packages('IRkernel', repos='https://cloud.r-project.org')\"",
            "R -e \"IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')\""
        ])
    
    # Install JavaScript Kernel if requested
    if "javascript" in kernels:
        template = template.run_cmd([
            "npm install -g --unsafe-perm git+https://github.com/e2b-dev/ijavascript.git",
            "ijsinstall --install=global"
        ])
    
    # Install Deno Kernel if requested
    if "deno" in kernels:
        template = template.run_cmd([
            "curl -fsSL https://deno.land/x/install/install.sh | sh",
            "export DENO_INSTALL=\"$HOME/.deno\"",
            "export PATH=\"$DENO_INSTALL/bin:$PATH\"",
            "deno jupyter --unstable --install"
        ])
        template = template.copy("deno.json", "/root/.local/share/jupyter/kernels/deno/kernel.json")
    
    # Install Bash Kernel if requested
    if "bash" in kernels:
        template = template.run_cmd([
            "pip install bash_kernel",
            "python -m bash_kernel.install"
        ])
    
    # Install Java and Java Kernel if requested
    if "java" in kernels:
        template = template.run_cmd([
            "apt-get update",
            "apt-get install -y default-jdk",
        ])
        template = template.run_cmd([
            "wget https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip",
            "unzip ijava-1.3.0.zip",
            "python install.py --sys-prefix"
        ])
    
    # Common setup steps (always run)
    template = (
        template
        # Create server virtual environment
        .run_cmd([
            "python -m venv /root/.server/.venv",
            "mkdir -p /root/.server/"
        ])
        # Copy and install server requirements
        .copy("server/requirements.txt", "/root/.server/requirements.txt")
        .run_cmd("/root/.server/.venv/bin/pip install --no-cache-dir -r /root/.server/requirements.txt")
        .copy("server", "/root/.server")
        # Copy configuration files
        .copy("matplotlibrc", "/root/.config/matplotlib/.matplotlibrc")
        .copy("start-up.sh", "/root/.jupyter/start-up.sh")
        .run_cmd("chmod +x /root/.jupyter/start-up.sh")
        .copy("jupyter_server_config.py", "/root/.jupyter/")
        .run_cmd("mkdir -p /root/.ipython/profile_default")
        .copy("ipython_kernel_config.py", "/root/.ipython/profile_default/")
        .run_cmd("mkdir -p /root/.ipython/profile_default/startup")
        .copy("startup_scripts", "/root/.ipython/profile_default/startup")
        .set_start_cmd("/root/.jupyter/start-up.sh", wait_for_port(49999))
    )
    
    return template
