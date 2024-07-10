FROM python:3.10

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl git util-linux jq sudo

ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  JUPYTER_CONFIG_PATH="/root/.jupyter" \
  IPYTHON_CONFIG_PATH="/root/.ipython" \
  SERVER_PATH="/root/.server"

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && ipython kernel install --name "python3" --user

RUN mkdir -p $SERVER_PATH/
COPY ./server/requirements.txt $SERVER_PATH
RUN pip install --no-cache-dir -r $SERVER_PATH/requirements.txt

COPY ./start-up.sh $JUPYTER_CONFIG_PATH/
RUN chmod +x $JUPYTER_CONFIG_PATH/start-up.sh

COPY ./jupyter_server_config.py $JUPYTER_CONFIG_PATH/

RUN mkdir -p $IPYTHON_CONFIG_PATH/profile_default
COPY ipython_kernel_config.py $IPYTHON_CONFIG_PATH/profile_default/

COPY ./server $SERVER_PATH

EXPOSE 8000

ENTRYPOINT $JUPYTER_CONFIG_PATH/start-up.sh
