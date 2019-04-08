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

RUN chmod 750 /code
RUN groupadd -g 999 appuser && useradd -m -r -u 999 -g appuser appuser
RUN cp /code/scripts/run.sh /home/appuser/
RUN chmod +x /home/appuser/run.sh

CMD run-agent
