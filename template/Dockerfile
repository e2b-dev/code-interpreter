FROM python:3.12

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq sudo fonts-noto-cjk

# Install Node.js 20.x from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV JUPYTER_CONFIG_PATH=/root/.jupyter
ENV IPYTHON_CONFIG_PATH=/root/.ipython
ENV SERVER_PATH=/root/.server
ENV R_VERSION=4.4.2
ENV R_HOME=/opt/R/4.4.2
ENV JAVA_HOME=/opt/java/openjdk

# Install Jupyter
COPY ./requirements.txt /root/requirements.txt
RUN pip install --no-cache-dir -r /root/requirements.txt && ipython kernel install --name "python3" --user

# R Kernel
RUN curl -O https://cdn.rstudio.com/r/debian-12/pkgs/r-${R_VERSION}_1_amd64.deb && sudo apt-get update && sudo apt-get install -y ./r-${R_VERSION}_1_amd64.deb && ln -s ${R_HOME}/bin/R /usr/bin/R
RUN R -e "install.packages('IRkernel', repos='https://cloud.r-project.org')"
RUN R -e "IRkernel::installspec(user = FALSE, name = 'r', displayname = 'R')"

# Javascript Kernel
RUN npm install -g --unsafe-perm git+https://github.com/e2b-dev/ijavascript.git
RUN ijsinstall --install=global

# Deno Kernel
RUN curl -fsSL https://deno.land/x/install/install.sh | DENO_INSTALL=/usr/local sh
RUN deno jupyter --unstable --install
COPY ./deno.json /root/.local/share/jupyter/kernels/deno/kernel.json

# Bash Kernel
RUN pip install bash_kernel
RUN python -m bash_kernel.install

# Create separate virtual environment for server
RUN python -m venv $SERVER_PATH/.venv

# Copy server and its requirements
RUN mkdir -p $SERVER_PATH/
COPY ./server/requirements.txt $SERVER_PATH
RUN $SERVER_PATH/.venv/bin/pip install --no-cache-dir -r $SERVER_PATH/requirements.txt
COPY ./server $SERVER_PATH

# Copy matplotlibrc
COPY matplotlibrc /root/.config/matplotlib/.matplotlibrc

# Copy Jupyter configuration
COPY ./start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh

COPY ./jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default/startup
COPY startup_scripts/ $IPYTHON_CONFIG_PATH/profile_default/startup


# Java Kernel
RUN apt-get update && apt-get install -y default-jdk
RUN wget https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip && \
    unzip ijava-1.3.0.zip && \
    python install.py --sys-prefix

# Setup entrypoint for local development
ENTRYPOINT $JUPYTER_CONFIG_PATH/start-up.sh