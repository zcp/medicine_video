from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class CrawlImportStatus(Base):
    """爬取导入任务状态表"""
    __tablename__ = "crawl_import_status"

    user_id = Column(UUID(as_uuid=True), primary_key=True, comment="用户ID")
    status = Column(String(20), nullable=False, default="running", comment="状态：running, completed, failed")
    progress = Column(JSONB, nullable=True, comment="进度信息（JSON格式）")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    __table_args__ = (
        Index("idx_crawl_import_status_updated_at", "updated_at"),
    )

