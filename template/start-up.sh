#!/bin/bash

echo "Starting Code Interpreter server..."
systemctl daemon-reload
systemctl start jupyter code-interpreter
