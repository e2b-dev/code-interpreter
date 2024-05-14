FROM python:3.10

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq

ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  JUPYTER_CONFIG_PATH="/root/.jupyter" \
  IPYTHON_CONFIG_PATH="/root/.ipython"


COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && ipython kernel install --name "python3" --user
COPY ./jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

COPY ./start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh



# Use the E2B-specific base image
FROM e2bdev/code-interpreter:latest

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Copy the requirements.txt file into the Docker image
COPY requirements.txt /tmp/requirements.txt

# Install Python packages from requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Install E2B CLI
RUN npm install -g @e2b/cli@latest

# Install additional Python packages
RUN pip install e2b_code_interpreter
RUN pip install litellm
RUN pip install gradio

# Ensure Jupyter is installed and configured
RUN pip3 install jupyter

# Create necessary Jupyter directories and files
RUN mkdir -p /root/.jupyter && \
    echo "c.NotebookApp.ip = '0.0.0.0'" > /root/.jupyter/jupyter_notebook_config.py

# Ensure Jupyter kernel is properly set up
RUN yes | jupyter notebook --generate-config && \
    jupyter kernelspec list

# Set the entrypoint to bash for interactive use
ENTRYPOINT ["/bin/bash"]
