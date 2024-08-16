start-template-server:
	docker run --rm -e E2B_LOCAL=true -p 49999:49999 -it $$(docker build -q ./template -f ./template/e2b.Dockerfile)
