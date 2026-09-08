#!/bin/sh
# ============================================================
# LiveCore 容器启动入口 — 分类优化 K7（阶段 3 部署自动化）
#
# 启动顺序（全部幂等，可安全重复执行）：
#   1. 建表        python -m app.init_db            （Base.metadata.create_all）
#   2. 迁移        python scripts/run_migrations.py （migration_log 防重放）
#   3. 分类种子    seed_categories()                （仅 35 条分类，不含专家/直播间种子）
#   4. 科室种子    python scripts/seed_expert_departments.py（128 条，存在即跳过）
#   5. 数据体检    python scripts/audit_category_integrity.py（异常仅告警，不阻断启动）
#   6. 启动服务    exec "$@"                        （转交 CMD: uvicorn）
#
# 设计决策（阶段 3 确认）：
#   - 只 seed 分类+科室，不执行全量 seed.py（避免生产库混入种子专家/直播间）
#   - 建表/迁移/分类种子失败 → 容器退出（restart 策略重试），保证数据安全
#   - audit 异常 → 打印告警继续启动（测试残留不阻断，由 CheckList 人工确认）
# ============================================================
set -e

echo "=========================================================="
echo "[entrypoint] LiveCore 启动初始化开始 $(date -u +%FT%TZ)"
echo "=========================================================="

# 1. 建表（幂等）
echo "[entrypoint] 1/5 建表..."
python -m app.init_db

# 2. 迁移（migration_log 防重放；历史迁移在首次部署时用 --baseline 标记）
echo "[entrypoint] 2/5 执行未应用的迁移..."
python scripts/run_migrations.py

# 3. 分类种子（仅 35 条常量分类，函数级调用，不执行 seed.py 全量）
echo "[entrypoint] 3/5 初始化分类种子（35 条）..."
python -c "
from app.database import SessionLocal
from app.seed import seed_categories
db = SessionLocal()
try:
    seed_categories(db)
    db.commit()
finally:
    db.close()
"

# 4. 科室种子（128 条标准科室，存在即跳过）
echo "[entrypoint] 4/5 初始化科室种子（128 条）..."
python scripts/seed_expert_departments.py

# 5. 数据体检（异常仅告警，不阻断）
echo "[entrypoint] 5/5 分类数据体检..."
if python scripts/audit_category_integrity.py; then
    echo "[entrypoint] 体检通过（未发现数据完整性问题）"
else
    echo "[entrypoint] ⚠️ 体检发现问题（详见上方输出）——服务仍将启动，请按部署 CheckList 处理"
fi

echo "=========================================================="
echo "[entrypoint] 初始化完成，启动服务: $*"
echo "=========================================================="

exec "$@"
