#!/bin/bash

function start_jupyter_server() {
	counter=0
	response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/status")
	while [[ ${response} -ne 200 ]]; do
		let counter++
		if ((counter % 20 == 0)); then
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

	cd /root/.server/
	/root/.server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors
}

export PATH="/opt/java/openjdk/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

echo "Starting Code Interpreter server..."
start_jupyter_server &
jupyter server --IdentityProvider.token="" >/dev/null
