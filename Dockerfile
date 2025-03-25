FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libasound2-dev

RUN pip install -r requirements.txt
