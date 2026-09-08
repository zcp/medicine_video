"""
搜索历史与热词统计模型
"""
import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Index, UniqueConstraint, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class UserSearchHistory(Base):
    """用户搜索历史表"""
    __tablename__ = "user_search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    keyword_norm = Column(String(255), nullable=False)
    search_count = Column(Integer, nullable=False, default=1)
    last_searched_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'keyword_norm', name='uq_user_search_history_user_keyword'),
        Index('idx_user_search_history_user_time', 'user_id', 'last_searched_at'),
    )


class SearchKeywordStats(Base):
    """搜索关键词统计表"""
    __tablename__ = "search_keyword_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword_norm = Column(String(255), nullable=False, unique=True)
    keyword = Column(String(255), nullable=True)  # 原始关键词（保留大小写）
    total_count = Column(BigInteger, nullable=False, default=0)
    last_searched_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_search_keyword_stats_count', 'total_count'),
    )
