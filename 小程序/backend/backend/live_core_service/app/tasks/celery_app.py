from celery import Celery
from app.core.config import settings

# 1. 创建一个被整个项目共享的 Celery app 实例
#    它的名字是 'live_core_worker'
app = Celery("live_core_worker")
