# Backend API application for flutter-based mobile app

## Product architecture
![](https://github.com/maxonclaxon/nikolife-backend/blob/master/readme_files/product_architecture.jpeg)
## Demo
![](https://github.com/maxonclaxon/nikolife-backend/blob/master/readme_files/app_demo.gif)

## Run
1) Prepare all dependencies with `make start`. It will create environment folder `./venv`, then start database and S3 (min.io) services. Database and S3 data will be stored in `./temp` folder. 
2) Change dev environment variables if you need to. `dev.env` file if you will use uvicorn server or `dev_containered.env` if you will run service in container
   1) ### Environment variables description
      1) #### Database
         1) `DATABASE__HOST - host address of postgres database (127.0.0.1). Requires postgres > 11.11`
         2) `DATABASE__PORT - database port (5432)`
         3) `DATABASE__USERNAME - databse username (db_user)`
         4) `DATABASE__PASSWORD - databse password for username (db_user_pass)`
         5) `DATABASE__NAME - database name (db_name)`
      2) #### S3 (AWS S3 API compatible cloud storage. I use min.io)
         1) `S3__HOST -  host (127.0.0.1)`
         2) `S3__ACCKEY - storage access key`
         3) `S3__SECKEY - storage secret key`
         4) `S3__ENDPOINT - aws S3 api compatible cloud storage endpoint (http://127.0.0.1:9000)`
         5) `S3__BUCKET - storage bucket (bucket)`
      3) #### Sentry
         1) `SENTRY__DSN - sentry dsn. Optional`
      4) #### Other
         1) `ENVIRONMENT= one of development / testin / production`
3) ### Run with development server (uvicorn)
   1) activate virtual environment: `source ./venv/bin/activate`
   2) load environment: `set -o allexport; . ./dev.env; set +o allexport;`
   3) use `uvicorn main:app --reload`
4) ### Run in docker
   1) build container: `docker build -t NAME_OF_CONTAINER`
   2) run container with environment file and do 8000-to-80 port forward: `docker run --rm -p 8000:80 --network nikolife-backend --env-file dev_containered.env NAME_OF_CONTAINER`

## Testing
You can test API with a postman. All  requests were exported with the collection file. You can find it in `./readme_files/nikolife.postman_collection.json`.
[Here is instruction how to import data to postman.](https://learning.postman.com/docs/getting-started/importing-and-exporting-data/#importing-data-into-postman)