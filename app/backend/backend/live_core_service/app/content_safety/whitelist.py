"""内容安全分类白名单（add-docs/12-13 §4）

命中规则后，若原文含该类白名单短语，仅撤销该类命中，不影响其他 category。
"""

from __future__ import annotations

import re
from typing import Dict, List

# category -> phrases[]
CONTENT_SAFETY_WHITELIST: Dict[str, List[str]] = {
    "absolute_superlative": [
        "第一次",
        "第一天",
        "第一周",
        "第一个月",
        "第一年",
        "第一排",
        "第一阶段",
        "第一步",
        "第一场",
        "第一节",
        "第一季",
        "独家直播",
        "独家回放",
        "独家专访",
        "完美收官",
        "完美结束",
        "完美落幕",
        "完美谢幕",
        "永不放弃",
        "永不言弃",
        "永久保存",
        "冠军杯",
        "冠军赛",
        "夺冠",
    ],
    "absolute_time_scale": [
        "终身学习",
        "终身成长",
        "永久删除",
        "永久保存",
        "终身成就",
    ],
    "cure_rate_quantified": [
        "有效期",
        "有效证件",
        "有效身份",
        "好评率",
        "出勤率",
        "到课率",
        "收视率",
    ],
    "medical_treatment_claim": [
        "治疗进展",
        "治疗方案讨论",
        "治疗经验分享",
        "规范治疗",
        "遵医嘱治疗",
        "不能代替治疗",
    ],
    "cosmetic_medical_claim": [
        "处方药科普",
        "处方药说明",
        "凭处方",
        "遵医嘱处方",
    ],
    "special_drug": [
        "全麻",
        "局麻",
        "局部麻醉",
        "麻醉科",
        "麻醉医生",
        "手术麻醉讲解",
    ],
    "porn_vulgar": [
        "裸辞",
        "裸考",
        "露出笑容",
        "露脸",
        "嫩豆腐",
        "新鲜嫩",
        "延时摄影",
        "延时拍摄",
        "增大字体",
        "音量增大",
    ],
    "abuse_discrimination": [
        "垃圾分类",
        "清理垃圾",
        "垃圾站",
        "垃圾邮件",
        "扔垃圾",
    ],
    "false_endorsement": [
        "邀请专家",
        "专家做客",
        "专家分享",
        "专家简介",
        "三甲医院工作",
        "就职于三甲",
    ],
    "financial_fraud": [
        "比特币是什么",
        "区块链科普",
        "虚拟货币风险提示",
    ],
    "gambling": [
        "反对赌博",
        "赌博危害",
        "禁赌",
    ],
}


def _normalize_phrase(value: str) -> str:
    lowered = value.lower().strip()
    return re.sub(r"[\s\-_·•.*]+", "", lowered)


def is_category_whitelisted(category: str, value: str, normalized: str) -> bool:
    """原文/规范化文本是否含该类白名单短语（仅撤销该类）"""
    if not category:
        return False
    phrases = CONTENT_SAFETY_WHITELIST.get(category)
    if not phrases:
        return False

    value_lower = value.lower()
    for phrase in phrases:
        if not phrase:
            continue
        if phrase.lower() in value_lower:
            return True
        pn = _normalize_phrase(phrase)
        if pn and pn in normalized:
            return True
    return False
