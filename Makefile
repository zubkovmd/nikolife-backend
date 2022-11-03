########## Variables
MINIO_SERVICE_USER := USERNAME
MINIO_SERVICE_PASSWORD := PASSWORD
MINIO_WEB_CONSOLE_PORT := 9001
# IF MODIFIED, THEN THIS VARIABLES SHOULD BE MODIFIED IN ENVIRONMENT FILES TOO (
## S3__PORT variable
MINIO_API_PORT := 9002
## DATABASE__PORT variable
DATABASE_PORT := 5432
# MODIFY IN ENVIRONMENT FILE FOR CONTAINER LAUNCH ONLY (dev_containered)
## SS3__HOST
S3_SERVICE_NAME := minio
## DATABASE__HOST
DATABASE_SERVICE_NAME := database


########## Install dependencies
install-dependencies: requirements.txt requirements-dev.txt
	virtualenv venv &&  \
	source ./venv/bin/activate && \
	python3 -m pip install --upgrade pip && \
	python3 -m pip install -r requirements.txt -r requirements-dev.txt && \
	source ./venv/bin/activate


########## Start dependent services
#### Start minio s3 service
start-minio: # Starting minio service
	echo 'Starting minio service'; \
	(docker network create nikolife-backend &> /dev/null || :) && \
	(docker stop $(S3_SERVICE_NAME) &> /dev/null && docker rm $(S3_SERVICE_NAME) &> /dev/null || :) && \
	(rm -r ./temp/minio_data &> /dev/null || :) && mkdir -p ./temp/minio_data && \
	docker run -p $(MINIO_API_PORT):9000 -p $(MINIO_WEB_CONSOLE_PORT):9001 -e MINIO_ROOT_USER=$(MINIO_SERVICE_USER) -e MINIO_ROOT_PASSWORD=$(MINIO_SERVICE_PASSWORD)  \
	-e MINIO_ACCESS_KEY=WAWDJAIWDAOPFPDWAPK -e MINIO_SECRET_KEY=WKDAKJWNDAKWJNDAKWDIADN \
	--network nikolife-backend --name $(S3_SERVICE_NAME) --platform linux/amd64 -v $(PWD)/temp/minio_data:/data -d\
	 quay.io/minio/minio server /data --console-address ":9001"

prepare-minio: start-minio
	echo 'Preparing minio service'; \
	docker run --rm --network nikolife-backend --link minio:minio -e MINIO_BUCKET=$MINIO_BUCKET --entrypoint sh minio/mc -c "\
	echo 'Wait minio to startup...' && \
	while ! curl http://$(S3_SERVICE_NAME):9000 &> /dev/null; do sleep 0.1; done; \
	sleep 5; mc config host add storage http://$(S3_SERVICE_NAME):9000 $(MINIO_SERVICE_USER) $(MINIO_SERVICE_PASSWORD) && \
	mc rm -r --force storage/test || true && \
	mc mb storage/test && \
	mc admin user add storage TESTUSERACCESSKEY TESTUSERSECRETKEY && \
	mc admin policy set storage readwrite user=TESTUSERACCESSKEY \
"

#### Start database
start-database: # Starting database service
	echo 'Starting database service'; \
	(docker network create nikolife-backend &> /dev/null || :) && \
	(docker stop $(DATABASE_SERVICE_NAME) &> /dev/null && docker rm $(DATABASE_SERVICE_NAME) &> /dev/null || :) && \
	(rm -r ../temp/pg_data &> /dev/null || :) && mkdir -p ./temp/pg_data && \
	docker run  -e POSTGRES_DB=postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
	--network nikolife-backend -v $(PWD)/temp/pg_data:/var/lib/postgresql/data \
	--name $(DATABASE_SERVICE_NAME) -d -p $(DATABASE_PORT):5432 postgres:11.11

prepare-database: install-dependencies start-database
	echo 'waiting database startup for 1 min...' && sleep 60; \
	echo 'Run database migrations';  \
	source ./venv/bin/activate && \
	set -o allexport && \
  	. ./dev.env && \
  	set +o allexport && \
	python3 app/alembic_upgrade_head.py

#### Start all dependent services
start: prepare-minio prepare-database

########## Stop dependent services
stop-minio: # Stopping minio service
	echo 'Stopping minio service' && \
	(docker stop $(S3_SERVICE_NAME) &> /dev/null && docker rm $(S3_SERVICE_NAME)  || :)
stop-database: # Stopping database service
	echo 'Stopping database service' && \
	(docker stop $(DATABASE_SERVICE_NAME) &> /dev/null && docker rm $(DATABASE_SERVICE_NAME)|| :)
stop-all: stop-minio stop-database

