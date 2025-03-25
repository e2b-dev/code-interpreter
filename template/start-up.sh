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

	python_response=$(curl -s -X POST "localhost:8888/api/sessions" -H "Content-Type: application/json" -d '{"path": "/home/user", "kernel": {"name": "python3"}, "type": "notebook", "name": "default"}')
	python_status=$(echo "${python_response}" | jq -r '.kernel.execution_state')
	if [[ ${python_status} != "starting" ]]; then
		echo "Error creating kernel: ${python_response} ${python_status}"
		exit 1
	fi

	sudo mkdir -p /root/.jupyter
	python_kernel_id=$(echo "${python_response}" | jq -r '.kernel.id')
	sudo echo "${python_kernel_id}" | sudo tee /root/.jupyter/kernel_id >/dev/null
	sudo echo "${python_response}" | sudo tee /root/.jupyter/.session_info >/dev/null

	# Warm up the Deno kernel
	deno_response=$(curl -s -X POST "localhost:8888/api/sessions" -H "Content-Type: application/json" -d '{"path": "/home/user/deno", "kernel": {"name": "deno"}, "type": "notebook", "name": "default"}')
	deno_status=$(echo "${deno_response}" | jq -r '.kernel.execution_state')
	if [[ ${deno_status} != "starting" ]]; then
		echo "Error creating kernel: ${deno_response} ${deno_status}"
		exit 1
	fi

	deno_session_id=$(echo "${deno_response}" | jq -r '.id')
	curl -s -X DELETE "localhost:8888/api/sessions/${deno_session_id}"

	cd /root/.server/
	/root/.server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors
}

echo "Starting Code Interpreter server..."
start_jupyter_server &
MATPLOTLIBRC=/root/.config/matplotlib/.matplotlibrc jupyter server --IdentityProvider.token="" >/dev/null 2>&1
