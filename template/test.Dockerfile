FROM python:3.10.14

ENV JAVA_HOME=/opt/java/openjdk
COPY --from=eclipse-temurin:11-jdk $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq sudo nodejs npm fonts-noto-cjk

ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  JUPYTER_CONFIG_PATH="/root/.jupyter" \
  IPYTHON_CONFIG_PATH="/root/.ipython" \
  SERVER_PATH="/root/.server"

# Install Jupyter
COPY ./template/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && ipython kernel install --name "python3" --user

# Javascript Kernel
RUN npm install -g node-gyp
RUN npm install -g --unsafe-perm ijavascript
RUN ijsinstall --install=global

# Deno Kernel
COPY --from=denoland/deno:bin-2.0.4 /deno /usr/bin/deno
RUN chmod +x /usr/bin/deno
RUN deno jupyter --unstable --install
COPY ./template/deno.json /root/.local/share/jupyter/kernels/deno/kernel.json

# Create separate virtual environment for server
RUN python -m venv $SERVER_PATH/.venv

# Copy server and its requirements
RUN mkdir -p $SERVER_PATH/
COPY ./template/server/requirements.txt $SERVER_PATH
RUN $SERVER_PATH/.venv/bin/pip install --no-cache-dir -r $SERVER_PATH/requirements.txt
COPY ./template/server $SERVER_PATH

# Copy matplotlibrc
COPY ./template/matplotlibrc /root/.config/matplotlib/matplotlibrc

# Copy Jupyter configuration
COPY ./template/start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh

COPY ./template/jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ./template/ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default/startup
COPY ./template/startup_scripts/* $IPYTHON_CONFIG_PATH/profile_default/startup

# Setup entrypoint for local development
WORKDIR /home/user
COPY ./chart_data_extractor ./chart_data_extractor
RUN pip install -e ./chart_data_extractor
ENTRYPOINT $JUPYTER_CONFIG_PATH/start-up.sh
