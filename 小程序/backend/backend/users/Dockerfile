FROM python:3.9.7-slim

WORKDIR /app
COPY requirements.txt .
RUN pip uninstall -y jwt || echo "No 'jwt' package to uninstall"

RUN pip install --no-cache-dir --retries 10 --default-timeout 120 -r requirements.txt -i https://pypi.org/simple

COPY . .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

CMD ["bash", "entrypoint.sh"]