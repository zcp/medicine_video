from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# 1. 创建一个被整个项目共享的 Celery app 实例
#    它的名字是 'live_core_worker'
app = Celery("live_core_worker")

# 2. 定时调度（阶段 3 M1）：每周分类体检
#    broker/backend 沿用现状（环境变量 CELERY_BROKER_URL / CELERY_RESULT_BACKEND 自动读取）
app.conf.beat_schedule = {
    "category-audit-weekly": {
        "task": "app.tasks.audit_task.audit_weekly",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # 每周日 03:00 UTC
    },
}
