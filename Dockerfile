FROM python:3.10-slim

RUN apt-get update -qq && \
    apt-get install curl -y
RUN apt-get install libsqlite3-mod-spatialite -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY ./src/convert.py .
COPY ./src/create_db.py .
COPY ./src/server.py .
COPY ./src/main.py .
RUN mkdir /data

CMD ["python", "/convert.py"]
