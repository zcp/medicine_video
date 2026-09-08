"""内容安全管理端 Schema 单元测试（回归：ContentScene 覆盖全部 seed 场景）"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.content_safety.medical_lexicon_seed import TEXT_FIELD_MATRIX
from app.content_safety.schemas import (
    ContentSafetyRuleItem,
    ContentSafetyRulePageResult,
)

ALL_SEED_SCENES = set(TEXT_FIELD_MATRIX.keys())


def _rule_row(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "rule_name": "test-rule",
        "scene": "message",
        "target_field": "content",
        "match_type": "keyword",
        "pattern": "加V",
        "action": "block",
        "severity": "high",
        "priority": 100,
        "enabled": True,
        "remark": None,
        "binding_level": "platform",
        "rule_category": "general",
        "regulation_ref": None,
        "created_by": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestContentSceneCoversSeedScenes:
    @pytest.mark.parametrize("scene", sorted(ALL_SEED_SCENES))
    def test_seed_scene_row_serializable(self, scene):
        """seed 会写库的每个 scene（含 tag_name）都必须能被 ContentSafetyRuleItem 反序列化"""
        row = _rule_row(scene=scene)
        item = ContentSafetyRuleItem.from_orm(row)
        assert item.scene == scene
        assert item.model_dump(mode="json")["scene"] == scene

    def test_tag_name_rule_roundtrip_via_real_seed_data(self):
        rule_data = {
            "rule_name": "tag_name-name-advertising_guidance",
            "scene": "tag_name",
            "target_field": "name",
            "match_type": "keyword",
            "pattern": "加V",
            "action": "warn",
            "severity": "medium",
            "priority": 100,
            "enabled": True,
            "remark": None,
            "binding_level": "platform",
            "rule_category": "advertising_guidance",
            "regulation_ref": None,
        }
        row = _rule_row(**rule_data)
        item = ContentSafetyRuleItem.from_orm(row)
        assert item.scene == "tag_name"

    def test_page_result_with_tag_name_rows(self):
        """回归 admin GET /content-safety/rules 崩溃路径：页内含 tag_name 行不得抛错"""
        rows = [_rule_row(scene="message"), _rule_row(scene="tag_name")]
        result = ContentSafetyRulePageResult(
            items=[ContentSafetyRuleItem.from_orm(r) for r in rows],
            total=2,
            page=1,
            page_size=20,
        )
        assert len(result.items) == 2
        assert result.model_dump(mode="json")["items"][1]["scene"] == "tag_name"

    def test_unknown_scene_still_rejected(self):
        """Literal 收紧语义不变：schema 之外的 scene 值仍应被拒绝"""
        with pytest.raises(ValidationError):
            ContentSafetyRuleItem.from_orm(_rule_row(scene="not_a_scene"))
