#!/bin/bash

function create_root_kernels() {
	# Get all installed kernels
	kernels=$(jupyter kernelspec list --json | jq -r '.kernelspecs | keys[]')
	
	for kernel in $kernels; do
		# Get the kernel directory
		kernel_dir=$(jupyter kernelspec list --json | jq -r ".kernelspecs[\"$kernel\"].resource_dir")
		
		# Create directory for root kernel if it doesn't exist
		root_kernel_dir="/usr/local/share/jupyter/kernels/${kernel}_root"
		sudo mkdir -p "$root_kernel_dir"
		
		# Copy all files from original kernel first
		sudo cp -r "$kernel_dir"/* "$root_kernel_dir/" 2>/dev/null || true
		
		# Create and write the modified kernel.json
		cat "$kernel_dir/kernel.json" | jq '.argv = ["sudo"] + .argv | .display_name = .display_name + " (root)"' | sudo tee "$root_kernel_dir/kernel.json" > /dev/null
		
		echo "Created root version of kernel: ${kernel}_root"
	done
}

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

	response=$(curl -s -X POST "localhost:8888/api/sessions" -H "Content-Type: application/json" -d '{"path": "'$HOME'", "kernel": {"name": "python3_root"}, "type": "notebook", "name": "default"}')
	status=$(echo "${response}" | jq -r '.kernel.execution_state')
	if [[ ${status} != "starting" ]]; then
		echo "Error creating kernel: ${response} ${status}"
		exit 1
	fi

	mkdir -p $HOME/.jupyter
	kernel_id=$(echo "${response}" | jq -r '.kernel.id')
	echo "${kernel_id}" > $HOME/.jupyter/kernel_id
	echo "${response}" > $HOME/.jupyter/.session_info

	cd $HOME/.server/
	$HOME/.server/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors --timeout-keep-alive 640
}

echo "Creating root versions of kernels..."
create_root_kernels

echo "Starting Code Interpreter server..."
start_jupyter_server &
MATPLOTLIBRC=$HOME/.config/matplotlib/.matplotlibrc jupyter server --IdentityProvider.token=""
