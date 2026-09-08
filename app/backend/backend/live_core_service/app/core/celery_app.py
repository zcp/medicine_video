from celery import Celery

# 在这里我们假设Celery的配置（如broker URL）是通过其他方式加载的
# 例如，从环境变量或配置文件中。
# 为简单起见，这里我们只创建一个Celery实例。

celery_app = Celery(
    "live_core_tasks",
    broker="redis://localhost:6379/0",  # 示例 Broker，实际应从配置中读取
    backend="redis://localhost:6379/0", # 示例 Backend，实际应从配置中读取
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