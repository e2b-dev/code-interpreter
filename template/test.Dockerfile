FROM python:3.10.14

ENV HOME=/home/user

ENV JAVA_HOME=/opt/java/openjdk
COPY --from=eclipse-temurin:11-jdk $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq nodejs npm fonts-noto-cjk sudo

# Create new user with root privileges while keeping root user
RUN useradd -m -s /bin/bash user && \
  echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
  echo 'user:password' | chpasswd && \
  usermod -aG sudo user

ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  JUPYTER_CONFIG_PATH="$HOME/.jupyter" \
  IPYTHON_CONFIG_PATH="$HOME/.ipython" \
  SERVER_PATH="$HOME/.server"

# Install Jupyter
COPY ./template/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && ipython kernel install --name "python3"

# Javascript Kernel
RUN npm install -g node-gyp
RUN npm install -g --unsafe-perm ijavascript
RUN ijsinstall --install=global

# Deno Kernel
COPY --from=denoland/deno:bin-2.0.4 /deno /usr/bin/deno
RUN chmod +x /usr/bin/deno
RUN deno jupyter --unstable --install && \
    mkdir -p /usr/local/share/jupyter/kernels/deno && \
    mv $HOME/.local/share/jupyter/kernels/deno/* /usr/local/share/jupyter/kernels/deno/ && \
    rmdir $HOME/.local/share/jupyter/kernels/deno

COPY ./template/deno.json /usr/local/share/jupyter/kernels/deno/kernel.json

# Create separate virtual environment for server
RUN python -m venv $SERVER_PATH/.venv

# Copy server and its requirements
RUN mkdir -p $SERVER_PATH/
COPY ./template/server/requirements.txt $SERVER_PATH
RUN $SERVER_PATH/.venv/bin/pip install --no-cache-dir -r $SERVER_PATH/requirements.txt
COPY ./template/server $SERVER_PATH

# Copy matplotlibrc
COPY ./template/matplotlibrc $HOME/.config/matplotlib/matplotlibrc

# Copy Jupyter configuration
COPY ./template/start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh

COPY ./template/jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ./template/ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default/startup
COPY ./template/startup_scripts/* $IPYTHON_CONFIG_PATH/profile_default/startup

# Setup entrypoint for local development
WORKDIR $HOME
COPY ./chart_data_extractor ./chart_data_extractor
RUN pip install -e ./chart_data_extractor

# Change ownership of all files to user
RUN chown -R user:user $HOME

USER user
ENTRYPOINT $JUPYTER_CONFIG_PATH/start-up.sh
