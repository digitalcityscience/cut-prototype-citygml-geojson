FROM python:3.10-slim

RUN apt-get update -qq && \
    apt-get install curl -y
RUN apt-get install libsqlite3-mod-spatialite -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY ./src/. ./src
RUN mkdir ./src/data
