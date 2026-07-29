#!/bin/bash
# Blocks until Jupyter Server is responsive, then records which Jupyter
# instance answered. jupyter-instance-check.sh compares against that recording
# to notice when Jupyter has been replaced.

MAX_RETRIES=50
RETRY_INTERVAL=0.2
INSTANCE_FILE=/run/jupyter-instance

for i in $(seq 1 $MAX_RETRIES); do
    # /api/status reports the server's start time, which is what identifies
    # this particular Jupyter process.
    started=$(curl -fsS -m 2 "http://localhost:8888/api/status" 2>/dev/null | jq -r '.started')

    if [ -n "$started" ] && [ "$started" != "null" ]; then
        echo "$started" >"$INSTANCE_FILE"
        echo "Jupyter Server is healthy"
        exit 0
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "Waiting for Jupyter Server to become healthy... (attempt $i/$MAX_RETRIES)"
    fi
    sleep $RETRY_INTERVAL
done

echo "Jupyter Server health check failed after $MAX_RETRIES attempts"
exit 1
