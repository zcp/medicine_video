"""内容安全引擎单元测试（含分层策略白名单 / 分档）"""

import uuid
from types import SimpleNamespace

from app.content_safety.engine import evaluate_field, normalize_text, rule_matches
from app.content_safety.medical_lexicon_data import (
    DROPPED_BARE_KEYWORDS,
    FRAUD_PATTERN,
    MEDICAL_LEXICON,
    build_medical_rules,
)
from app.content_safety.tier import resolve_action, resolve_tier


def _rule(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "rule_name": "test",
        "match_type": "keyword",
        "pattern": "加V",
        "action": "block",
        "severity": "high",
        "priority": 100,
        "target_field": "content",
        "rule_category": "general",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _rules_for_scene_field(scene: str, field: str):
    matrix = {scene: [field]}
    built = build_medical_rules(matrix)
    return [
        SimpleNamespace(
            id=uuid.uuid4(),
            **{k: v for k, v in r.items() if k != "remark"},
            remark=r.get("remark"),
        )
        for r in built
        if r["enabled"]
    ]


class TestContentSafetyEngine:
    def test_normalize_text(self):
        assert normalize_text("加 V") == "加v"

    def test_url_block(self):
        rule = _rule(match_type="url", pattern="builtin", target_field="nickname", rule_name="外链")
        assert rule_matches(rule, "visit http://abc.com")

    def test_contact_phone_block(self):
        rule = _rule(match_type="contact", pattern="builtin", target_field="nickname", rule_name="联系方式")
        assert rule_matches(rule, "我的手机13800138000")

    def test_fraud_keyword_block(self):
        rule = _rule(
            match_type="fraud",
            pattern="加V,私聊",
            target_field="content",
            rule_name="广告词",
            rule_category="framework_fraud",
        )
        decision, matched, message = evaluate_field([rule], "content", "欢迎加V私聊")
        assert decision == "block"
        assert matched
        assert "广告引流" in message
        assert "请修改后重试" in message
        assert "广告词" not in message

    def test_allow_normal_text(self):
        rule = _rule(match_type="fraud", pattern="加V", target_field="content")
        decision, matched, _ = evaluate_field([rule], "content", "大家好")
        assert decision == "allow"
        assert not matched

    def test_avatar_internal_allowed(self):
        rule = _rule(
            match_type="image_meta",
            pattern="internal_only",
            target_field="avatar_url",
            rule_name="头像外链",
        )
        assert not rule_matches(rule, "/uploads/avatars/a.png")

    def test_avatar_external_blocked(self):
        rule = _rule(
            match_type="image_meta",
            pattern="internal_only",
            target_field="avatar_url",
            rule_name="头像外链",
        )
        assert rule_matches(rule, "https://abc.com/a.png")

    def test_medical_absolute_superlative_warn_on_tier_a(self):
        rule = _rule(
            match_type="keyword",
            pattern=MEDICAL_LEXICON["absolute_superlative"]["pattern"],
            target_field="content",
            rule_name="message-content-absolute_superlative",
            priority=11,
            action="warn",
            rule_category="absolute_superlative",
        )
        decision, matched, _ = evaluate_field([rule], "content", "全网第一的产品")
        assert decision == "warn"
        assert matched

    def test_medical_cure_rate_regex_block(self):
        rule = _rule(
            match_type="regex",
            pattern=MEDICAL_LEXICON["cure_rate_quantified"]["pattern"],
            target_field="content",
            rule_name="message-content-cure_rate_quantified",
            priority=11,
            rule_category="cure_rate_quantified",
        )
        assert rule_matches(rule, "治愈率90%")

    def test_political_sensitive_local_fallback(self):
        rule = _rule(
            match_type="political",
            pattern="台独,港独,分裂国家",
            target_field="content",
            rule_name="message-content-political_sensitive",
            priority=5,
            rule_category="political_sensitive",
        )
        decision, matched, _ = evaluate_field([rule], "content", "支持台独")
        assert decision == "block"
        assert matched


class TestLayeredStrategyWhitelist:
    def test_first_live_allow_after_drop(self):
        rules = _rules_for_scene_field("room_title", "title")
        decision, matched, _ = evaluate_field(rules, "title", "这是我第一次直播")
        assert decision == "allow"
        assert not matched

    def test_perfect_ending_whitelist(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "完美收官")
        assert decision == "allow"
        assert not matched

    def test_exclusive_live_whitelist(self):
        rules = _rules_for_scene_field("room_title", "title")
        decision, matched, _ = evaluate_field(rules, "title", "独家直播今晚八点")
        assert decision == "allow"
        assert not matched

    def test_garbage_sort_allow(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "请做好垃圾分类")
        assert decision == "allow"
        assert not matched

    def test_timelapse_allow(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "延时摄影分享")
        assert decision == "allow"
        assert not matched

    def test_valid_period_whitelist(self):
        rules = _rules_for_scene_field("room_tab", "text_content")
        decision, matched, _ = evaluate_field(rules, "text_content", "有效期 30 天")
        assert decision == "allow"
        assert not matched

    def test_treatment_progress_not_blocked_by_bare_word(self):
        rules = _rules_for_scene_field("room_title", "title")
        decision, matched, _ = evaluate_field(rules, "title", "今天讲高血压治疗进展")
        assert decision in ("allow", "warn")
        assert decision != "block"

    def test_blood_pressure_monitor_not_hard_block(self):
        rules = _rules_for_scene_field("room_description", "description")
        decision, matched, _ = evaluate_field(rules, "description", "血压仪怎么用")
        assert decision in ("allow", "warn")


class TestLayeredStrategyBlock:
    def test_cure_all_block(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "包治百病")
        assert decision == "block"
        assert matched

    def test_fraud_block(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "加V私聊返利")
        assert decision == "block"

    def test_political_block(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "台独")
        assert decision == "block"

    def test_superlative_warn_on_a(self):
        rules = _rules_for_scene_field("room_title", "title")
        decision, matched, _ = evaluate_field(rules, "title", "全网第一款科普课")
        assert decision == "warn"
        assert matched

    def test_adult_product_block(self):
        rules = _rules_for_scene_field("message", "content")
        decision, matched, _ = evaluate_field(rules, "content", "私处护理成人专用")
        assert decision == "block"


class TestTierAndPatterns:
    def test_resolve_tier_room_tab_fields(self):
        assert resolve_tier("room_tab", "title") == "A"
        assert resolve_tier("room_tab", "text_content") == "B"
        assert resolve_tier("room_tab", "tab_key") == "D"
        assert resolve_tier("search_query", "keyword") == "D"
        assert resolve_tier("room_description", "description") == "B"

    def test_d_tier_disables_ad_medical(self):
        assert resolve_action("absolute_superlative", "D") is None
        assert resolve_action("medical_treatment_claim", "D") is None
        assert resolve_action("framework_fraud", "D") == "warn"
        assert resolve_action("political_sensitive", "D") == "block"

    def test_search_query_weak_seed(self):
        rules = build_medical_rules({"search_query": ["keyword"]})
        disabled = [r for r in rules if not r["enabled"]]
        assert disabled
        assert all(r["rule_category"] != "political_sensitive" or r["enabled"] for r in rules)
        abs_rules = [r for r in rules if r["rule_category"] == "absolute_superlative"]
        assert abs_rules and not abs_rules[0]["enabled"]

    def test_dropped_bare_keywords_absent(self):
        """裸词不得以逗号分隔独立词出现在 pattern 中（防误伤回归审计）"""
        for category, meta in MEDICAL_LEXICON.items():
            if meta["match_type"] == "regex":
                continue
            parts = {p.strip() for p in meta["pattern"].split(",") if p.strip()}
            for bare in DROPPED_BARE_KEYWORDS:
                assert bare not in parts, f"{category} still has bare '{bare}'"

        fraud_parts = {p.strip() for p in FRAUD_PATTERN.split(",") if p.strip()}
        assert "优惠" not in fraud_parts
        assert "兼职" not in fraud_parts
