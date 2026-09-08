"""statutory 规则管理端约束单元测试"""

from types import SimpleNamespace

import pytest

from app.content_safety.crud import _validate_rule_update
from app.content_safety.exceptions import ContentSafetyValidationError


def _rule(**kwargs):
    defaults = {
        "binding_level": "statutory",
        "rule_category": "absolute_superlative",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestStatutoryRuleConstraints:
    def test_statutory_disable_forbidden(self):
        with pytest.raises(ContentSafetyValidationError, match="禁止停用"):
            _validate_rule_update(_rule(), {"enabled": False})

    def test_statutory_warn_action_allowed(self):
        """分层策略 V1.1：statutory 允许 warn"""
        _validate_rule_update(_rule(), {"action": "warn"})

    def test_statutory_allow_action_forbidden(self):
        with pytest.raises(ContentSafetyValidationError, match="仅允许 block 或 warn"):
            _validate_rule_update(_rule(), {"action": "allow"})

    def test_political_sensitive_pattern_forbidden(self):
        with pytest.raises(ContentSafetyValidationError, match="political_sensitive"):
            _validate_rule_update(
                _rule(rule_category="political_sensitive"),
                {"pattern": "新词1,新词2"},
            )

    def test_platform_warn_allowed(self):
        _validate_rule_update(
            _rule(binding_level="platform", rule_category="cheat_gray"),
            {"action": "warn", "pattern": "测试warn"},
        )

    def test_statutory_other_pattern_allowed(self):
        _validate_rule_update(
            _rule(rule_category="absolute_superlative"),
            {"pattern": "新词1,新词2"},
        )
