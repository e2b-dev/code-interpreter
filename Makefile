start-template-server:
	docker run --rm -e LOCAL=true -p 49999:49999 -it $$(docker build -q ./template -f ./template/e2b.Dockerfile)
