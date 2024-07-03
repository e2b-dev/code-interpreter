.PHONY: generate
generate:
	rm -rf ./python/e2b_code_interpreter/client
	npx -yes @openapitools/openapi-generator-cli@latest version-manager set 7.1.0
	npx -yes @openapitools/openapi-generator-cli generate \
	-i openapi.yml  \
	-g python \
	-o ./python/e2b_code_interpreter/client  \
	--global-property apis,models,supportingFiles,modelDocs=false \
	--additional-properties=generateSourceCodeOnly=true \
	--additional-properties=disallowAdditionalPropertiesIfNotPresent=false \
	--additional-properties=usePydanticV2=true \
	--additional-properties=packageName=e2b_code_interpreter.client
	mv ./python/e2b_code_interpreter/client/e2b_code_interpreter/client/* ./python/e2b_code_interpreter/client
	rm -r ./python/e2b_code_interpreter/client/docs
	rm -r .//python/e2b_code_interpreter/client/test
	rm -r ./python/e2b_code_interpreter/client/.openapi-generator
	rm -r ./python/e2b_code_interpreter/client/e2b_code_interpreter
	rm -r ./python/e2b_code_interpreter/client/.openapi-generator-ignore
	black .


	rm -rf ./template/server/models/*
	npx -yes @openapitools/openapi-generator-cli@latest version-manager set 7.1.0
	npx -yes @openapitools/openapi-generator-cli generate \
	-i openapi.yml  \
	-g python \
	-o ./template/server/tmp  \
	--global-property apis=false,models,supportingFiles=false,modelDocs=false \
	--additional-properties=disallowAdditionalPropertiesIfNotPresent=false \
	--additional-properties=usePydanticV2=true \
	--additional-properties=packageName=models
	mv ./template/server/tmp/models/* ./template/server
	rm -r ./template/server/tmp
	black .
