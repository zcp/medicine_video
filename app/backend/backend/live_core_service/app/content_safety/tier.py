"""内容安全场景分档与 action 矩阵（add-docs/12-13 §1–§2）"""

from __future__ import annotations

from typing import Dict, Optional

# 档位 action：None 表示该档不启用该类 seed（enabled=false）
TierAction = Optional[str]  # "block" | "warn" | None

# rule_category -> {A,B,C,D} -> action | None
ACTION_MATRIX: Dict[str, Dict[str, TierAction]] = {
    "political_sensitive": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "gambling": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "controlled_substance": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "porn_vulgar": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "framework_url": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "framework_contact": {"A": "block", "B": "block", "C": "block", "D": "warn"},
    "framework_fraud": {"A": "block", "B": "block", "C": "block", "D": "warn"},
    "absolute_superlative": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "absolute_time_scale": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "absolute_false_promise": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "cure_rate_quantified": {"A": "warn", "B": "block", "C": "block", "D": None},
    "medical_treatment_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "cosmetic_medical_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "wellness_false_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "medical_device_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "special_drug": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "prescription_drug": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "military_name": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "food_false_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "baby_false_claim": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "home_false_claim": {"A": "warn", "B": "block", "C": "block", "D": None},
    "false_endorsement": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "counterfeit_infringement": {"A": "warn", "B": "block", "C": "block", "D": None},
    "cosmetic_surgery": {"A": "warn", "B": "warn", "C": "block", "D": None},
    "abuse_discrimination": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "privacy_gray": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "cheat_gray": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "platform_circumvention": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "superstition": {"A": "warn", "B": "block", "C": "block", "D": None},
    "financial_fraud": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "mlm_fraud": {"A": "block", "B": "block", "C": "block", "D": "block"},
    "loan_fraud": {"A": "block", "B": "block", "C": "block", "D": "block"},
}

# scene → 默认档；room_tab 按字段细分
_SCENE_TIER = {
    "message": "A",
    "room_title": "A",
    "nickname": "A",
    "room_description": "B",
    "search_query": "D",
    "brand_product": "C",
    "expert_profile": "B",
}

_ROOM_TAB_FIELD_TIER = {
    "title": "A",
    "text_content": "B",
    "tab_key": "D",
}

LAYERED_STRATEGY_REMARK = "分层策略V1.1；见 12-13-内容安全分层策略-V1"


def resolve_tier(scene: str, field: str) -> str:
    """scene + field → 档位 A/B/C/D"""
    if scene == "room_tab":
        return _ROOM_TAB_FIELD_TIER.get(field, "A")
    return _SCENE_TIER.get(scene, "A")


def resolve_action(category: str, tier: str) -> TierAction:
    """按矩阵取 action；未知类别默认 block"""
    row = ACTION_MATRIX.get(category)
    if not row:
        return "block"
    return row.get(tier, "block")
