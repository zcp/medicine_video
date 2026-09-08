from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.crawl_import_status import CrawlImportStatus
import logging

logger = logging.getLogger(__name__)


def save_crawl_import_status(db: Session, user_id: UUID, status: str, progress: dict) -> bool:
    """
    保存爬取导入任务状态
    
    使用 PostgreSQL INSERT ... ON CONFLICT DO UPDATE 实现一个用户一条记录的自动覆盖
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        status: 状态字符串（'running', 'completed', 'failed'）
        progress: 进度字典（包含 start_time, end_time, result, error 等）
    
    Returns:
        bool: 是否保存成功。失败时返回 False，不抛异常（不影响主流程）
    """
    try:
        stmt = insert(CrawlImportStatus).values(
            user_id=user_id,
            status=status,
            progress=progress,
            updated_at=datetime.utcnow()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'status': stmt.excluded.status,
                'progress': stmt.excluded.progress,
                'updated_at': stmt.excluded.updated_at
            }
        )
        db.execute(stmt)
        db.commit()
        user_id_for_logging = str(user_id)
        logger.info(f"状态保存成功 - User: {user_id_for_logging}, Status: {status}")
        return True
    except Exception as e:
        db.rollback()
        user_id_for_logging = str(user_id)
        logger.error(f"状态保存失败 - User: {user_id_for_logging}, Error: {str(e)}", exc_info=True)
        # 状态更新失败不应该影响主流程（记录警告日志）
        return False


def get_crawl_import_status(db: Session, user_id: UUID) -> Optional[dict]:
    """
    获取爬取导入任务状态
    
    Args:
        db: 数据库会话
        user_id: 用户ID
    
    Returns:
        dict | None: 状态字典，如果不存在返回 None
        {
            "status": "running" | "completed" | "failed",
            "progress": { ... },
            "updated_at": "2025-11-19T10:00:00Z"
        }
    """
    try:
        print("h1")
        record = db.query(CrawlImportStatus).filter(
            CrawlImportStatus.user_id == user_id
        ).first()

        print("h2")
        if not record:
            return None

        print("h3")
            # 【添加调试日志位置1】在这里添加

        return {
            "status": record.status,
            "progress": record.progress,  # JSONB 自动转换为 dict
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }
    except Exception as e:
        user_id_for_logging = str(user_id)
        logger.error(f"状态查询失败 - User: {user_id_for_logging}, Error: {str(e)}", exc_info=True)
        return None


def check_running_task(db: Session, user_id: UUID, max_running_hours: int = 3) -> bool:
    """
    检查用户是否有正在运行的爬取导入任务（用于并发控制）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        max_running_hours: 最大运行时间（小时），超过此时间且状态仍为running，视为异常状态，允许新任务
    
    Returns:
        bool: True 表示有正在运行的任务，False 表示没有
    """
    try:
        record = db.query(CrawlImportStatus).filter(
            CrawlImportStatus.user_id == user_id,
            CrawlImportStatus.status == 'running'
        ).first()
        
        if not record:
            return False
        
        # 检查是否超过最大运行时间（异常状态处理）
        if record.updated_at:
            max_time = datetime.utcnow() - timedelta(hours=max_running_hours)
            if record.updated_at < max_time:
                # 超过最大运行时间，视为异常状态，允许新任务
                user_id_for_logging = str(user_id)
                logger.warning(
                    f"用户 {user_id_for_logging} 的任务状态异常："
                    f"状态为 running 但已超过 {max_running_hours} 小时，"
                    f"最后更新时间为 {record.updated_at}"
                )
                return False
        
        return True
    except Exception as e:
        user_id_for_logging = str(user_id)
        logger.error(f"检查运行任务失败 - User: {user_id_for_logging}, Error: {str(e)}", exc_info=True)
        # 异常情况下，为了安全，返回 True（阻止新任务）
        return True

