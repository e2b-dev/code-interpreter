#!/bin/bash

trap 'echo "Jupyter exited, killing code-interpreter..."; pkill -f "uvicorn main:app"' EXIT

exec /usr/local/bin/jupyter server --IdentityProvider.token=""
