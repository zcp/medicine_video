"""
LiveCore Service - Session Processing Tasks

This module contains Celery tasks for processing live sessions
after streaming ends, including video processing and data archiving.
"""

import uuid
import time
import logging
import asyncio


from sqlalchemy.ext.asyncio import AsyncSession

# 1. 从共享的 celery_app.py 中导入唯一的 app 实例
from .celery_app import app as celery_app

# 2. 从统一的 database.py 导入异步数据库会话生成器
from app.database import get_db as get_async_db
from app.crud import session as crud_session
from app.models.live_core import LiveSessionStatus
from app.schemas.live_core import LiveSessionUpdate

logger = logging.getLogger(__name__)

# --- 3. 移除独立的、硬编码的数据库配置和会话函数 ---
# DATABASE_URL = "..."  <-- 已删除
# async def get_async_db_session()... <-- 已删除


# 4. (核心修改) 将业务逻辑函数改造为接收 db 会话参数
async def _process_session_async(db: AsyncSession, session_id: str) -> dict:
    """
    异步处理直播会话的内部函数。
    它现在依赖于调用者传入一个有效的数据库会话。
    """
    session_uuid = uuid.UUID(session_id)
    logger.info(f"[TASK_LOGIC] 开始处理: session_id={session_uuid}")

    try:
        # 直接使用传入的 db 对象，不再自己创建
        session = await crud_session.get(db, session_id=session_uuid)
        if not session:
            logger.error(f"会话不存在: session_id={session_uuid}")
            return {"status": "error", "message": "Session not found"}

        logger.info(f"找到会话: session_id={session_uuid}, status={session.status}")

        # 更新状态为processing
        await crud_session.update(db, db_obj=session, obj_in=LiveSessionUpdate(status=LiveSessionStatus.PROCESSING))
        logger.info(f"会话状态已更新为processing: session_id={session_uuid}")

        # 执行核心处理任务
        try:
            logger.info(f"开始执行视频处理任务: session_id={session_uuid}")
            # 使用 asyncio.sleep 来模拟异步IO等待
            await asyncio.sleep(5)
            logger.info(f"视频处理任务完成: session_id={session_uuid}")

            # 更新状态为ready
            await crud_session.update(db, db_obj=session, obj_in=LiveSessionUpdate(status=LiveSessionStatus.READY))
            logger.info(f"会話状态已更新为ready: session_id={session_uuid}")

            return {
                "status": "success",
                "session_id": str(session_uuid),
                "final_status": "ready"
            }

        except Exception as processing_error:
            logger.error(f"视频处理任务失败: session_id={session_uuid}, error={processing_error}")

            # 失败时更新状态为error
            # 此处无需重新查询session，因为它仍在同一个db会话的上下文中
            await crud_session.update(db, db_obj=session, obj_in=LiveSessionUpdate(status=LiveSessionStatus.ERROR))
            logger.error(f"会话状态已更新为error: session_id={session_uuid}")

            return {
                "status": "error",
                "session_id": str(session_uuid),
                "final_status": "error"
            }

    except Exception as e:
        logger.error(f"后台任务执行失败: session_id={session_uuid}, error={e}")
        # 重新抛出异常，以便 Celery 感知到任务失败
        raise


# ... (文件顶部的其他 imports 和 _process_session_async 函数保持不变) ...

# ✅ 修改点：使用同步函数定义 Celery 任务
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def post_stream_processing_task(self, session_id: str):
    """
    同步入口任务，负责启动异步逻辑。
    """
    logger.info(f"[CELERY_TASK] 收到任务，准备执行: session_id={session_id}")

    # 使用 asyncio.run() 来运行异步逻辑
    return asyncio.run(_run_async_task(session_id))


async def _run_async_task(session_id: str):
    """
    异步包装函数，负责管理数据库连接并调用主逻辑
    """
    async_db_gen = get_async_db()
    db: AsyncSession = await async_db_gen.__anext__()

    try:
        return await _process_session_async(db, session_id)
    finally:
        await db.close()
        logger.info(f"[CELERY_TASK] 数据库连接已关闭: session_id={session_id}")
# --- 6. (可选) 移除与当前核心功能无关的额外任务示例 ---
# @celery_app.task
# def cleanup_old_sessions_task(): ...

# @celery_app.task
# def generate_session_report_task(session_id: str): ...