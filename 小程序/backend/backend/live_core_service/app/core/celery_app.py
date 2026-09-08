import os
from celery import Celery

# 从环境变量读取 Redis 配置，Docker 容器中使用服务名 "redis"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "live_core_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.session_processing"],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
) 