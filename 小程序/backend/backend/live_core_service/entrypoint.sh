#!/bin/bash
set -e

echo "[live_core] 初始化数据库表..."
python -m app.init_db

echo "[live_core] 写入医学合规内容安全规则..."
python - <<'PY'
import asyncio
from app.database import AsyncSessionLocal
from app.content_safety.medical_lexicon_seed import run_medical_lexicon_seed

async def run():
    async with AsyncSessionLocal() as session:
        changed = await run_medical_lexicon_seed(session)
        await session.commit()
        print(f"[live_core] 医学合规规则 seed 完成，变更 {changed} 条（含新增/更新）")

asyncio.run(run())
PY

echo "[live_core] 启动 uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
