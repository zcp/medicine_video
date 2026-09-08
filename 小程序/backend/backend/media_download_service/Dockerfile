FROM python:3.9.7-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 --default-timeout 120 -r requirements.txt -i https://pypi.org/simple

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]