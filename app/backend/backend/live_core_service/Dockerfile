FROM python:3.9.7-slim

WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# sitecustomize.py 在 Python 启动时自动执行，确保 /app 在 sys.path 中
# 解决 pytest 7.4.3 conftest 发现机制的 PYTHONPATH 问题
COPY sitecustomize.py /usr/local/lib/python3.9/site-packages/sitecustomize.py

COPY . .

# K7: 部署自动化入口（阶段 3）——建表/迁移/分类种子/科室种子/体检后启动服务
# entrypoint.sh 最后 exec "$@" 转交下方 CMD
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# 假设入口文件是 app/main.py，变量名 app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]