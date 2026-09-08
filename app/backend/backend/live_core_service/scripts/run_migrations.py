"""
统一迁移执行入口 — 分类优化 K4

按文件名顺序执行 migrations/ 目录下的 SQL 迁移文件，
已执行的迁移记录在 migration_log 表中（防重放、防编号冲突、留执行痕迹）。

用法（容器内）:
    cd /app && python scripts/run_migrations.py              # 执行所有未执行的迁移
    cd /app && python scripts/run_migrations.py --baseline   # 将现有文件全部标记为已执行（首次部署时，不实际执行）
    cd /app && python scripts/run_migrations.py --dry-run    # 仅列出待执行迁移，不执行

说明:
    - 历史迁移（V4-V16）已在各环境手动执行过，首次接入时用 --baseline 标记，
      避免在已有数据的环境上重放历史迁移。
    - 之后新增迁移文件自动纳入执行流程。
"""
import glob
import os
import sys
import logging
from datetime import datetime

from sqlalchemy import text
from app.database import engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "migrations")


def ensure_migration_log() -> None:
    """确保 migration_log 表存在"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS migration_log (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'applied',
                detail TEXT,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))


def get_applied_migrations() -> set:
    """返回已执行的迁移文件名集合"""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT migration_name FROM migration_log")).fetchall()
    return {r[0] for r in rows}


def list_migration_files() -> list:
    """按文件名顺序列出迁移文件"""
    files = glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))
    return sorted(os.path.basename(f) for f in files)


def apply_migration(filename: str) -> None:
    """执行单个迁移文件并记录"""
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
        conn.execute(
            text("INSERT INTO migration_log (migration_name, status, detail) VALUES (:name, 'applied', :detail)"),
            {"name": filename, "detail": f"executed at {datetime.now().isoformat(timespec='seconds')}"},
        )
    logger.info(f"✅ 已执行: {filename}")


def main() -> int:
    args = sys.argv[1:]
    baseline = "--baseline" in args
    dry_run = "--dry-run" in args

    ensure_migration_log()
    files = list_migration_files()
    applied = get_applied_migrations()

    pending = [f for f in files if f not in applied]
    logger.info(f"迁移文件共 {len(files)} 个，已执行 {len(applied)} 个，待执行 {len(pending)} 个")

    if dry_run:
        for f in pending:
            logger.info(f"  ⏳ 待执行: {f}")
        return 0

    if baseline:
        with engine.begin() as conn:
            for f in pending:
                conn.execute(
                    text("INSERT INTO migration_log (migration_name, status, detail) VALUES (:name, 'baseline', :detail)")
                    .execution_options(synchronize_session=False),
                    {"name": f, "detail": "baseline marked (not executed)"},
                )
        logger.info(f"✅ 已标记基线 {len(pending)} 个（未实际执行）")
        return 0

    for f in pending:
        apply_migration(f)

    logger.info("🎉 全部迁移执行完毕")
    return 0


if __name__ == "__main__":
    sys.exit(main())
