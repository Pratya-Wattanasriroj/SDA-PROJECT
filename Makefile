cat <<EOF > Makefile
build:
	docker build -t my-web-app .

run:
	docker run -d -p 80:80 my-web-app

deploy: build
	-docker stop \$(docker ps -aq)
	-docker rm \$(docker ps -aq)
	\$(MAKE) run
EOF