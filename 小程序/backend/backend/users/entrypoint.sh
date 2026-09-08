#!/bin/bash
set -e

echo "[users] 初始化数据库表..."
python -m app.init_db

echo "[users] 写入医学合规内容安全规则..."
python - <<'PY'
import asyncio
from app.init_db import seed_content_safety
asyncio.run(seed_content_safety())
PY

echo "[users] 启动 uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8002
