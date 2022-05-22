FROM python:3.9

ENV HOME=/code

RUN apt-get update -y && apt-get upgrade -y && apt-get install netcat -y && apt-get install postgresql-client -y
RUN pip install --upgrade pip
RUN addgroup web && adduser web --home $HOME --ingroup web
RUN mkdir /var/log/waiters/ && chown -R web:web /var/log/waiters

WORKDIR $HOME

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /usr/local/bin

COPY ./src/ .

USER web
