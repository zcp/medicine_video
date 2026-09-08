"""
分类数据完整性每周体检任务 — 阶段 3 M1

通过 Celery Beat 每周触发，调用 scripts/audit_category_integrity.py 的体检逻辑。
告警方式（决策 3-B）：日志输出 + 任务结果（退出码 0/1），不引入外部告警通道。

执行入口（celery worker 需 --include=app.tasks.audit_task）:
    celery -A app.tasks.celery_app worker --include=app.tasks.session_processing,app.tasks.audit_task -l info

Beat 调度配置在 app/tasks/celery_app.py 的 beat_schedule 中（每周日 03:00 UTC）。
"""
import logging

from .celery_app import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.audit_task.audit_weekly")
def audit_weekly() -> dict:
    """每周分类数据完整性体检。

    返回:
        {"exit_code": 0/1, "summary": str} — 0=无异常；1=发现问题（见 worker 日志明细）
    """
    import scripts.audit_category_integrity as audit

    logger.info("开始每周分类体检（audit_category_integrity）...")
    try:
        exit_code = audit.main()
        summary = "未发现数据完整性问题" if exit_code == 0 else "发现数据完整性问题（详见日志）"
        logger.info(f"每周分类体检完成: exit_code={exit_code}, {summary}")
        return {"exit_code": exit_code, "summary": summary}
    except Exception as e:  # noqa: BLE001
        logger.exception(f"每周分类体检执行异常: {e}")
        return {"exit_code": 1, "summary": f"体检执行异常: {e}"}
