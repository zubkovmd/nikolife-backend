FROM python:3.10

WORKDIR /proj
COPY requirements.txt /proj/
RUN python -m pip install setuptools==57.5.0
RUN python -m pip install -r requirements.txt

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install locales
RUN echo "u_RU.UTF-8 UTF-8" >> /etc/locale.ge
ENV locale-gen ru_RU ru_RU.UTF-8

COPY ./app /proj/app
COPY main.py init.sh /proj/
RUN chmod +x /proj/init.sh


ENV TZ="Europe/Moscow"
ENTRYPOINT ["/proj/init.sh"]
