"""
专家科室受控词表 — 数据库模型

将 department 从自由文本升级为受控词表 FK。
每个科室名全局唯一，同义词存储在 synonyms JSONB 数组中。
科室 → 分类的映射在 category_id 中，是唯一的真相源。
"""
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ExpertDepartment(Base):
    """
    专家科室受控词表

    取代 experts.department 自由文本字段，确保每个科室名全局唯一。
    同义词列表通过 synonyms JSONB 存储，导入时直接匹配即可，不需要管理者手动创建。
    is_verified 标记是否为已审核的标准科室。
    """
    __tablename__ = "expert_departments"

    # 核心标识
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                comment='主键UUID，在应用层生成')

    # 标准科室名称 — 全局唯一（唯一约束由 DDL 级别保证，ORM 用 unique=True）
    name = Column(String(120), nullable=False, unique=True,
                  comment='标准科室名称，全局唯一，如"乳腺外科"、"冠脉介入组"')

    # 科室 → 分类映射（唯一真相源）
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        comment='科室所属的主分类ID。RESTRICT 防止误删关联的分类'
    )

    # 同义词列表（JSONB 数组）
    synonyms = Column(JSONB, nullable=False, default=list,
                      comment='同义词列表 JSON 数组，如 ["乳腺科","乳房外科"]')

    # 业务字段
    is_active = Column(Boolean, nullable=False, default=True,
                       comment='是否启用。false 表示该科室不再用于新专家')
    is_verified = Column(Boolean, nullable=False, default=False,
                         comment='是否已审核。false=自适应创建待确认，true=已审核标准词')

    # 来源追踪
    source = Column(String(50), nullable=True,
                    comment='创建来源：auto_match, csv_import, manual_create, admin_api, seed_v4, seed_s4, unknown_legacy')
    created_by = Column(UUID(as_uuid=True), nullable=True, default=None,
                        comment='创建人 user_id。auto_match 来源时为 NULL')

    # 时间戳
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        Index('idx_expert_departments_category_id', 'category_id'),
        Index('idx_expert_departments_is_active', 'is_active'),
        Index('idx_expert_departments_is_verified', 'is_verified'),
        Index('idx_expert_departments_source', 'source'),
        Index('idx_expert_departments_created_by', 'created_by'),
    )

    # 关联关系
    category = relationship("Category", lazy="select")

    # non-persistent helper（CRUD 层动态填充）
    expert_count = 0

    def __repr__(self):
        return f"<ExpertDepartment(id={self.id}, name={self.name})>"
