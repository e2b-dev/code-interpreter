.PHONY: generate
generate:
	# Generate Python client
	pipx install openapi-python-client
	rm -rf ./python/e2b_code_interpreter/client
	openapi-python-client generate --path openapi.yml --output-path ./python/e2b_code_interpreter/client
	mv ./python/e2b_code_interpreter/client/e2b_code_interpreter_client/* ./python/e2b_code_interpreter/client

	rm  ./python/e2b_code_interpreter/client/.gitignore ./python/e2b_code_interpreter/client/pyproject.toml ./python/e2b_code_interpreter/client/README.md ./python/e2b_code_interpreter/client/py.typed
	rm -rf ./python/e2b_code_interpreter/client/e2b_code_interpreter_client
	black .


start-template-server:
	docker run --rm -p 49999:49999 -it $$(docker build -q ./template -f ./template/e2b.Dockerfile)
