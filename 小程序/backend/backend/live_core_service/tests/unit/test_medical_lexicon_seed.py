"""医学合规词库 seed 单元测试"""

from app.content_safety.medical_lexicon_data import MEDICAL_LEXICON, FRAMEWORK_RULES, build_medical_rules
from app.content_safety.medical_lexicon_seed import MEDICAL_RULES, TEXT_FIELD_MATRIX
from app.content_safety.tier import resolve_tier


class TestMedicalLexiconSeed:
    def test_lexicon_category_count(self):
        assert len(MEDICAL_LEXICON) == 29
        assert len(FRAMEWORK_RULES) == 3

    def test_live_core_rule_count(self):
        fields = sum(len(f) for f in TEXT_FIELD_MATRIX.values())
        assert fields == 7
        assert len(MEDICAL_RULES) == fields * 32

    def test_rule_naming_convention(self):
        sample = MEDICAL_RULES[0]
        assert sample["rule_name"] == f"{sample['scene']}-{sample['target_field']}-{sample['rule_category']}"

    def test_statutory_binding_has_critical_severity(self):
        statutory = [r for r in MEDICAL_RULES if r["binding_level"] == "statutory"]
        assert statutory
        assert all(r["severity"] == "critical" for r in statutory)

    def test_build_medical_rules_users_matrix(self):
        users_matrix = {"nickname": ["nickname", "bio"]}
        rules = build_medical_rules(users_matrix)
        assert len(rules) == 64

    def test_tier_actions_on_message(self):
        abs_rules = [
            r for r in MEDICAL_RULES
            if r["scene"] == "message" and r["rule_category"] == "absolute_superlative"
        ]
        assert abs_rules
        assert abs_rules[0]["action"] == "warn"
        assert abs_rules[0]["enabled"] is True

    def test_search_query_d_tier_disables_superlative(self):
        abs_rules = [
            r for r in MEDICAL_RULES
            if r["scene"] == "search_query" and r["rule_category"] == "absolute_superlative"
        ]
        assert abs_rules
        assert abs_rules[0]["enabled"] is False

    def test_room_tab_field_tiers(self):
        assert resolve_tier("room_tab", "title") == "A"
        title_abs = next(
            r for r in MEDICAL_RULES
            if r["rule_name"] == "room_tab-title-absolute_superlative"
        )
        text_abs = next(
            r for r in MEDICAL_RULES
            if r["rule_name"] == "room_tab-text_content-absolute_superlative"
        )
        key_abs = next(
            r for r in MEDICAL_RULES
            if r["rule_name"] == "room_tab-tab_key-absolute_superlative"
        )
        assert title_abs["action"] == "warn"
        assert text_abs["action"] == "warn"
        assert key_abs["enabled"] is False
