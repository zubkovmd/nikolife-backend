# Backend API application for flutter-based mobile app

## Description
Here you can see a demo of the application:  
![](https://github.com/maxonclaxon/nikolife-backend/blob/master/readme_files/app_demo.gif)

## Run
1) ### Define environment variables 
   1) #### Database
      1) `DATABASE__HOST - host address of postgres database (127.0.0.1). Requires postgres > 11.11`
      2) `DATABASE__PORT - database port (5432)`
      3) `DATABASE__USERNAME - databse username (db_user)`
      4) `DATABASE__PASSWORD - databse password for username (db_user_pass)`
      5) `DATABASE__NAME - database name (db_name)`
   2) #### S3 (aws S3 api compatible cloud storage. I use min.io)
      1) `S3__HOST -  host (127.0.0.1)`
      2) `S3__ACCKEY - storage access key`
      3) `S3__SECKEY - storage secret key`
      4) `S3__ENDPOINT - aws S3 api compatible cloud storage endpoint (http://127.0.0.1:9000)`
      5) `S3__BUCKET - storage bucket (bucket)`
   3) #### Sentry
      1) `SENTRY__DSN - sentry dsn. Optional`
   4) #### Other
      1) `ENVIRONMENT= one of development / testin / production`
2) ### Run for development
   1) use `uvicorn main:app --reload`
3) ### Run in docker (-- TODO --) 