#!/bin/bash

echo "Waiting for Jupyter server to be ready..."
until curl -s -o /dev/null -w '%{http_code}' http://localhost:8888/api/status | grep -q '200'; do
  sleep 0.5
done
echo "Jupyter server is ready, starting Code Interpreter..."

echo $$ > /var/run/code-interpreter.pid
exec /root/.server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors --timeout-keep-alive 640
