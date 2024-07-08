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

	response=$(curl -s -X POST "localhost:8888/api/sessions" -H "Content-Type: application/json" -d '{"path": "/home/user", "kernel": {"name": "python3"}, "type": "notebook", "name": "default"}')
	status=$(echo "${response}" | jq -r '.kernel.execution_state')
	if [[ ${status} != "starting" ]]; then
		echo "Error creating kernel: ${response} ${status}"
		exit 1
	fi

	sudo mkdir -p /root/.jupyter
  kernel_id=$(echo "${response}" | jq -r '.kernel.id')
	sudo echo "${kernel_id}" | sudo tee /root/.jupyter/kernel_id >/dev/null
	sudo echo "${response}" | sudo tee /root/.jupyter/.session_info >/dev/null

	fastapi run /root/.server/main.py --port 8000 > /dev/null 2>&1
}

echo "Starting Code Interpreter server..."
start_jupyter_server &
jupyter server --IdentityProvider.token="" > /dev/null 2>&1
