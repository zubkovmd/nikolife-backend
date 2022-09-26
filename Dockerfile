FROM python:3.10

WORKDIR /proj

COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY entrypoint.sh entrypoint.sh
COPY app app

RUN chmod +x entrypoint.sh

ENTRYPOINT [ "entrypoint.sh" ]