#!/bin/bash

function start_jupyter_server() {
	counter=0
	response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/status")
	while [[ ${response} -ne 200 ]]; do
	  let counter++
	  if  (( counter % 20 == 0 )); then
      echo "Waiting for Jupyter Server to start..."
      sleep 0.1
    fi

		response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/status")
	done
	echo "Jupyter Server started"

	response=$(curl -s -X POST "localhost:8888/api/sessions" -H "Content-Type: application/json" -d '{"path": "/home/user", "kernel": {"name": "python3"}, "notebook": {"name": "default.ipynb"}, "type": "notebook", "name": "default"}')
	status=$(echo "${response}" | jq -r '.kernel.execution_state')
	if [[ ${status} != "starting" ]]; then
		echo "Error creating kernel: ${response} ${status}"
		exit 1
	fi
	echo "Kernel created"

  cat <<EOF >/home/user/default.ipynb
{
  "metadata": {
      "signature": "hex-digest",
      "kernel_info": {"name": "python3"},
      "language_info": {
          "name": "python3",
          "version": "3.10.14"
      }
  },
  "nbformat": 4,
  "nbformat_minor": 0,
  "cells": []
}
EOF

	sudo mkdir -p /root/.jupyter
  kernel_id=$(echo "${response}" | jq -r '.kernel.id')
	sudo echo "${kernel_id}" | sudo tee /root/.jupyter/kernel_id >/dev/null
	sudo echo "${response}" | sudo tee /root/.jupyter/.session_info >/dev/null
	echo "Jupyter Server started"
}

echo "Starting Jupyter Server..."
start_jupyter_server &
jupyter lab --IdentityProvider.token="" \
  --YDocExtension.ystore_class=pycrdt_websocket.ystore.TempFileYStore\
  --YDocExtension.document_save_delay=0.5 \
  --YDocExtension.document_cleanup_delay=None \
  --notebook-dir=/home/user \
  --LabApp.default_url='/doc'
