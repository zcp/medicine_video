"""内容安全数据库模型"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TIMESTAMP,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class ContentSafetyRule(Base):
    """内容安全规则表"""

    __tablename__ = "content_safety_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="规则ID")
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    scene = Column(String(50), nullable=False, comment="适用场景")
    target_field = Column(String(50), nullable=False, comment="目标字段")
    match_type = Column(String(30), nullable=False, comment="匹配类型")
    pattern = Column(Text, nullable=False, comment="匹配模式")
    action = Column(String(20), nullable=False, default="block", comment="决策动作")
    severity = Column(String(20), nullable=False, default="high", comment="严重级别")
    priority = Column(Integer, nullable=False, default=100, comment="优先级，数值越小越优先")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    remark = Column(String(500), nullable=True, comment="备注")
    binding_level = Column(
        String(20), nullable=False, default="platform", comment="强制级别：statutory/platform"
    )
    rule_category = Column(String(50), nullable=False, default="general", comment="违禁词分类编码")
    regulation_ref = Column(String(200), nullable=True, comment="法规/规范溯源")
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.public_id", ondelete="SET NULL"),
        nullable=True,
        comment="创建人 public_id",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('block', 'warn', 'allow')", name="chk_content_safety_rules_action"
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="chk_content_safety_rules_severity",
        ),
        CheckConstraint(
            "match_type IN ('keyword', 'regex', 'url', 'contact', 'html', 'political', "
            "'porn', 'gambling', 'fraud', 'image_meta')",
            name="chk_content_safety_rules_match_type",
        ),
        CheckConstraint(
            "binding_level IN ('statutory', 'platform')",
            name="chk_content_safety_rules_binding_level",
        ),
        Index("idx_content_safety_rules_scene_enabled_priority", "scene", "enabled", "priority"),
        Index("idx_content_safety_rules_target_field", "target_field"),
        Index("idx_content_safety_rules_created_by", "created_by"),
        Index("idx_content_safety_rules_category_enabled", "rule_category", "enabled"),
        Index("uq_content_safety_rules_rule_name", "rule_name", unique=True),
    )


class ContentSafetyLog(Base):
    """内容安全审计日志表"""

    __tablename__ = "content_safety_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="日志ID")
    scene = Column(String(50), nullable=False, comment="场景")
    resource_type = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(UUID(as_uuid=True), nullable=True, comment="资源ID")
    target_field = Column(String(50), nullable=False, comment="目标字段")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.public_id", ondelete="SET NULL"),
        nullable=True,
        comment="用户 public_id",
    )
    input_excerpt = Column(String(500), nullable=True, comment="输入摘要")
    normalized_excerpt = Column(String(500), nullable=True, comment="标准化摘要")
    decision = Column(String(20), nullable=False, comment="决策结果")
    matched_rule_ids = Column(JSONB, nullable=True, comment="命中规则ID列表")
    matched_rule_names = Column(JSONB, nullable=True, comment="命中规则名称列表")
    reason_code = Column(String(20), nullable=True, comment="原因码")
    reason_message = Column(String(500), nullable=True, comment="原因说明")
    request_id = Column(String(100), nullable=True, comment="请求ID")
    client_ip = Column(String(64), nullable=True, comment="客户端IP")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), comment="创建时间"
    )

    __table_args__ = (
        CheckConstraint(
            "decision IN ('allow', 'warn', 'block')", name="chk_content_safety_logs_decision"
        ),
        Index("idx_content_safety_logs_scene_created", "scene", "created_at"),
        Index("idx_content_safety_logs_user_created", "user_id", "created_at"),
        Index("idx_content_safety_logs_resource", "resource_type", "resource_id"),
        Index("idx_content_safety_logs_decision_created", "decision", "created_at"),
    )
