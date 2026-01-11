FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends gcc

RUN pip install -r requirements.txt

# オプション: テスト環境でテスト依存関係をインストール
RUN pip install -r requirements-dev.txt

COPY . .

CMD ["gunicorn", "--workers", "3", "--timeout", "120", "--bind", "0.0.0.0:8000", "app:app"]
