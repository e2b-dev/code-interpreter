FROM python:3.10.14

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq sudo nodejs npm fonts-noto-cjk

RUN mkdir -p /home/user/.jupyter /home/user/.ipython /home/user/.server

ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  JUPYTER_CONFIG_PATH="/home/user/.jupyter" \
  IPYTHON_CONFIG_PATH="/home/user/.ipython" \
  SERVER_PATH="/home/user/.server" \
  R_VERSION=4.4.2

ENV R_HOME=/opt/R/${R_VERSION} \
    JAVA_HOME=/opt/java/openjdk

# Install Jupyter
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && ipython kernel install --name "python3" --user

# R Kernel
# RUN curl -O https://cdn.rstudio.com/r/debian-12/pkgs/r-${R_VERSION}_1_amd64.deb && sudo apt-get update && sudo apt-get install -y ./r-${R_VERSION}_1_amd64.deb && ln -s ${R_HOME}/bin/R /usr/bin/R
# RUN R -e "install.packages('IRkernel', repos='https://cloud.r-project.org')"
# RUN R -e "IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')"

# Javascript Kernel
RUN npm install -g node-gyp
RUN npm install -g --unsafe-perm ijavascript
RUN ijsinstall --install=global

# Deno Kernel
COPY --from=denoland/deno:bin-2.0.4 /deno /usr/bin/deno
RUN chmod +x /usr/bin/deno
RUN deno jupyter --unstable --install
COPY ./deno.json /home/user/.local/share/jupyter/kernels/deno/kernel.json

# Bash Kernel
RUN pip install bash_kernel
RUN python -m bash_kernel.install

# Create separate virtual environment for server
RUN python -m venv $SERVER_PATH/.venv

# Copy server and its requirements
COPY ./server/requirements.txt $SERVER_PATH
RUN $SERVER_PATH/.venv/bin/pip install --no-cache-dir -r $SERVER_PATH/requirements.txt
COPY ./server $SERVER_PATH

# Copy matplotlibrc
COPY matplotlibrc /home/user/.config/matplotlib/.matplotlibrc

# Copy Jupyter configuration
COPY ./start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh

COPY ./jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default/startup
COPY startup_scripts/* $IPYTHON_CONFIG_PATH/profile_default/startup


COPY --from=eclipse-temurin:11-jdk $JAVA_HOME $JAVA_HOME
RUN ln -s ${JAVA_HOME}/bin/java /usr/bin/java

# Java Kernel
RUN wget https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip && \
    unzip ijava-1.3.0.zip && \
    python install.py --sys-prefix

# Setup entrypoint for local development
ENTRYPOINT $JUPYTER_CONFIG_PATH/start-up.sh
