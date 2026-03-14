#!/bin/bash

/usr/local/bin/jupyter server --IdentityProvider.token=""

# Jupyter exited — kill code-interpreter so supervisord restarts both
echo "Jupyter exited, killing code-interpreter..."
kill "$(cat /var/run/code-interpreter.pid)" 2>/dev/null
