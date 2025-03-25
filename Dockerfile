FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc

RUN pip install -r requirements.txt

RUN apt-get install -y timidity

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
