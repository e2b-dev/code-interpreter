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
