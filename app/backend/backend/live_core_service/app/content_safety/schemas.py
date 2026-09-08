"""内容安全 Pydantic Schemas"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


@dataclass(frozen=True)
class ContentSafetyRuleSnapshot:
    id: UUID
    rule_name: str
    target_field: str
    match_type: str
    pattern: str
    action: str
    severity: str
    priority: int
    rule_category: str = "general"
    regulation_ref: Optional[str] = None

    @classmethod
    def from_orm(cls, rule: Any) -> "ContentSafetyRuleSnapshot":
        return cls(
            id=rule.id,
            rule_name=rule.rule_name,
            target_field=rule.target_field,
            match_type=rule.match_type,
            pattern=rule.pattern,
            action=rule.action,
            severity=rule.severity,
            priority=rule.priority,
            rule_category=getattr(rule, "rule_category", "general") or "general",
            regulation_ref=getattr(rule, "regulation_ref", None),
        )


ContentScene = Literal[
    "nickname",
    "message",
    "room_title",
    "room_description",
    "room_tab",
    "search_query",
    "tag_name",
]


class ContentSafetyItem(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=50)
    value: str = Field(..., min_length=1)

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        return value.strip()


class ContentSafetyCheckRequest(BaseModel):
    scene: ContentScene
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: Optional[UUID] = None
    items: List[ContentSafetyItem] = Field(..., min_length=1)


class ContentSafetyMatchInfo(BaseModel):
    rule_id: UUID
    rule_name: str
    match_type: str
    severity: str
    action: str


class ContentSafetyFieldResult(BaseModel):
    field_name: str
    decision: Literal["allow", "warn", "block"]
    message: Optional[str] = None
    matched_rules: List[ContentSafetyMatchInfo] = Field(default_factory=list)


class ContentSafetyCheckResult(BaseModel):
    passed: bool
    decision: Literal["allow", "warn", "block"]
    results: List[ContentSafetyFieldResult]
    log_id: Optional[UUID] = None


class ContentSafetyRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    scene: ContentScene
    target_field: str = Field(..., min_length=1, max_length=50)
    match_type: str = Field(..., min_length=1, max_length=30)
    pattern: str = Field(..., min_length=1)
    action: Literal["block", "warn", "allow"] = "block"
    severity: Literal["low", "medium", "high", "critical"] = "high"
    priority: int = Field(default=100, ge=1, le=10000)
    enabled: bool = True
    remark: Optional[str] = Field(None, max_length=500)
    binding_level: Literal["statutory", "platform"] = "platform"
    rule_category: Optional[str] = Field(None, max_length=50)
    regulation_ref: Optional[str] = Field(None, max_length=200)


class ContentSafetyRuleCreate(ContentSafetyRuleBase):
    pass


class ContentSafetyRuleUpdate(BaseModel):
    pattern: Optional[str] = Field(None, min_length=1)
    action: Optional[Literal["block", "warn", "allow"]] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    priority: Optional[int] = Field(None, ge=1, le=10000)
    enabled: Optional[bool] = None
    remark: Optional[str] = Field(None, max_length=500)
    binding_level: Optional[Literal["statutory", "platform"]] = None
    rule_category: Optional[str] = Field(None, max_length=50)
    regulation_ref: Optional[str] = Field(None, max_length=200)


class ContentSafetyRuleItem(ContentSafetyRuleBase):
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, rule: Any) -> "ContentSafetyRuleItem":
        base = cls.model_validate(rule)
        base.enabled = getattr(rule, "enabled", True)
        return base


class ContentSafetyRulePageResult(BaseModel):
    items: List[ContentSafetyRuleItem]
    total: int
    page: int
    page_size: int


class ContentSafetyLogQueryParams(BaseModel):
    scene: Optional[str] = None
    resource_type: Optional[str] = None
    user_id: Optional[UUID] = None
    decision: Optional[Literal["allow", "warn", "block"]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ContentSafetyLogItem(BaseModel):
    id: UUID
    scene: str
    resource_type: str
    resource_id: Optional[UUID] = None
    target_field: str
    user_id: Optional[UUID] = None
    input_excerpt: Optional[str] = None
    normalized_excerpt: Optional[str] = None
    decision: str
    matched_rule_ids: Optional[list] = None
    matched_rule_names: Optional[list] = None
    reason_code: Optional[str] = None
    reason_message: Optional[str] = None
    client_ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("matched_rule_ids", "matched_rule_names", mode="before")
    @classmethod
    def parse_csv_list(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [x.strip() for x in v.split(",") if x.strip()]
            return parts if parts else None
        return v


class ContentSafetyLogPageResult(BaseModel):
    items: List[ContentSafetyLogItem]
    total: int
    page: int
    page_size: int
