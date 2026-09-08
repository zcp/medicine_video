"""内容安全面向用户的文案（最小化友好提示）"""

from __future__ import annotations

from typing import Optional

# rule_category → 中文备注（与《12-13》表 B0 对齐）
CATEGORY_LABELS = {
    "framework_url": "外链",
    "framework_contact": "联系方式",
    "framework_fraud": "广告引流话术",
    "absolute_superlative": "绝对化用语",
    "absolute_time_scale": "极限时间/规模用语",
    "absolute_false_promise": "虚假承诺用语",
    "cure_rate_quantified": "疗效量化宣称",
    "medical_treatment_claim": "疾病治疗类宣称",
    "cosmetic_medical_claim": "医美功效宣称",
    "wellness_false_claim": "养生虚假功效宣称",
    "medical_device_claim": "医疗器械相关用语",
    "special_drug": "特殊药品相关用语",
    "prescription_drug": "处方药名",
    "military_name": "军队名义用语",
    "porn_vulgar": "低俗擦边内容",
    "political_sensitive": "政治敏感内容",
    "gambling": "涉赌内容",
    "controlled_substance": "涉毒/管制相关内容",
    "financial_fraud": "虚假金融话术",
    "mlm_fraud": "传销/暴富话术",
    "loan_fraud": "贷款诈骗话术",
    "abuse_discrimination": "辱骂/歧视/暴力内容",
    "food_false_claim": "食品虚假功效宣称",
    "baby_false_claim": "母婴虚假功效宣称",
    "home_false_claim": "家居夸大功效宣称",
    "counterfeit_infringement": "侵权假冒相关用语",
    "false_endorsement": "虚假资质背书",
    "privacy_gray": "隐私灰产相关内容",
    "cheat_gray": "作弊刷单相关内容",
    "cosmetic_surgery": "医美整形相关用语",
    "platform_circumvention": "绕过平台交易话术",
    "superstition": "封建迷信相关内容",
    "general": "违规内容",
}

FIELD_LABELS = {
    "title": "标题",
    "description": "简介",
    "content": "内容",
    "nickname": "昵称",
    "bio": "个人简介",
    "keyword": "搜索词",
    "tab_key": "Tab 标识",
    "text_content": "正文",
    "name": "名称",
    "avatar_url": "头像",
}


def field_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name or "内容")


def category_label(category: Optional[str]) -> str:
    if not category:
        return CATEGORY_LABELS["general"]
    return CATEGORY_LABELS.get(category, "违规内容")


def build_block_message(field_name: str, category: Optional[str] = None) -> str:
    """用户可读的拦截文案（不暴露内部 rule_name）"""
    return (
        f"{field_label(field_name)}未通过审核：疑似含{category_label(category)}，请修改后重试"
    )


def build_political_block_message(field_name: str = "content") -> str:
    return (
        f"{field_label(field_name)}未通过审核：疑似含政治敏感内容，请修改后重试"
    )
