FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3.6 python3-pip
RUN pip3 install virtualenv

COPY . /code
WORKDIR /code

ENV PYTHONUNBUFFERED 1
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN pip3 install -r requirements.txt
RUN pip3 install .

CMD run-agent
