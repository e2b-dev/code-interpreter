#!/bin/bash

echo "Starting Code Interpreter server..."
supervisord -c /etc/supervisord.conf
