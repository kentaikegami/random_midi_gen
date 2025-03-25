FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libasound2-dev

RUN pip install -r requirements.txt

RUN apt-get install -y timidity

COPY . .

CMD ["gunicorn", "--workers", "3", "--timeout", "120", "--bind", "0.0.0.0:5001", "app:app"]
