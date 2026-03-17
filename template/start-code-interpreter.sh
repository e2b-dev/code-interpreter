#!/bin/bash

echo "Waiting for Jupyter server to be ready..."
retries=0
max_retries=20
until curl -s -o /dev/null -w '%{http_code}' http://localhost:8888/api/status | grep -q '200'; do
  retries=$((retries + 1))
  if [ "$retries" -ge "$max_retries" ]; then
    echo "Jupyter server failed to start after $max_retries retries"
    exit 1
  fi
  sleep 0.5
done
echo "Jupyter server is ready, starting Code Interpreter..."

echo $$ > /var/run/code-interpreter.pid
exec /root/.server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors --timeout-keep-alive 640
