"""内容安全规则匹配引擎"""

import re
from typing import Any, List, Optional, Tuple

from app.content_safety.schemas import ContentSafetyMatchInfo
from app.content_safety.whitelist import is_category_whitelisted
from app.content_safety.messages import build_block_message

ACTION_RANK = {"allow": 1, "warn": 2, "block": 3}
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}

URL_PATTERN = re.compile(
    r"(?i)(https?://|www\.|t\.me/|bit\.ly/|tinyurl\.|\.com/|\.cn/|\.net/)"
)
CONTACT_PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
CONTACT_QQ_PATTERN = re.compile(r"\b[1-9][0-9]{4,11}\b")
CONTACT_WECHAT_PATTERN = re.compile(r"(?i)(vx|wx|wechat|加v|加微|微信号|微信)")
HTML_PATTERN = re.compile(r"(?i)(<[^>]+>|javascript:|onerror=|onload=|<script)")

AVATAR_ALLOWED_PREFIXES = (
    "/uploads/avatars/",
    "/uploads/",
    "https://cdn.example.com/avatars/",
    "https://oss.example.com/avatars/",
)


def normalize_text(value: str) -> str:
    """去除空白与常见插符，用于关键词变体匹配"""
    lowered = value.lower().strip()
    return re.sub(r"[\s\-_·•.*]+", "", lowered)


def _match_keyword(pattern: str, value: str, normalized: str) -> bool:
    keywords = [k.strip() for k in pattern.split(",") if k.strip()]
    for keyword in keywords:
        kw = keyword.lower()
        if kw in value.lower() or kw in normalized:
            return True
    return False


def _match_regex(pattern: str, value: str) -> bool:
    try:
        return bool(re.search(pattern, value, re.IGNORECASE))
    except re.error:
        return False


def _match_url(value: str) -> bool:
    if URL_PATTERN.search(value):
        return True
    custom = r"(?i)https?://|www\.|t\.me/|bit\.ly/|tinyurl\."
    return bool(re.search(custom, value))


def _match_contact(value: str) -> bool:
    return bool(
        CONTACT_PHONE_PATTERN.search(value)
        or CONTACT_QQ_PATTERN.search(value)
        or CONTACT_WECHAT_PATTERN.search(value)
    )


def _match_html(value: str) -> bool:
    return bool(HTML_PATTERN.search(value))


def _match_image_meta(value: str, pattern: str) -> bool:
    """头像只允许内部可控地址；命中表示违规（外链）"""
    if not value:
        return False
    if value.startswith(AVATAR_ALLOWED_PREFIXES):
        return False
    if value.startswith("/") and not value.startswith(("http://", "https://")):
        return False
    if re.match(r"(?i)https?://", value):
        return True
    if pattern and pattern != "internal_only":
        return _match_regex(pattern, value)
    return not value.startswith(AVATAR_ALLOWED_PREFIXES)


def rule_matches(rule: Any, value: str) -> bool:
    normalized = normalize_text(value)
    match_type = rule.match_type

    if match_type == "keyword":
        return _match_keyword(rule.pattern, value, normalized)
    if match_type == "regex":
        return _match_regex(rule.pattern, value)
    if match_type == "url":
        if rule.pattern and rule.pattern not in ("builtin", "default"):
            return _match_regex(rule.pattern, value) or _match_url(value)
        return _match_url(value)
    if match_type == "contact":
        if rule.pattern and rule.pattern not in ("builtin", "default"):
            return _match_regex(rule.pattern, value) or _match_contact(value)
        return _match_contact(value)
    if match_type == "html":
        return _match_html(value) or _match_regex(rule.pattern, value)
    if match_type == "image_meta":
        return _match_image_meta(value, rule.pattern)
    if match_type in ("political", "porn", "gambling", "fraud"):
        return _match_keyword(rule.pattern, value, normalized)
    return False


def pick_final_decision(rule_entries: List[Tuple[Any, ContentSafetyMatchInfo]]) -> str:
    if not rule_entries:
        return "allow"

    min_priority = min(rule.priority for rule, _ in rule_entries)
    candidates = [(rule, info) for rule, info in rule_entries if rule.priority == min_priority]
    best_rule, _ = max(
        candidates,
        key=lambda pair: (
            ACTION_RANK.get(pair[1].action, 0),
            SEVERITY_RANK.get(pair[1].severity, 0),
        ),
    )
    return best_rule.action


def evaluate_field(
    rules: List[Any],
    field_name: str,
    value: str,
) -> Tuple[str, List[ContentSafetyMatchInfo], Optional[str]]:
    """对单个字段执行规则匹配，返回 (decision, matched_rules, message)

    分类白名单：命中后若原文含该类白名单短语，仅撤销该类命中，不影响其他 category。
    """
    matched_entries: List[Tuple[Any, ContentSafetyMatchInfo]] = []
    normalized = normalize_text(value)

    for rule in rules:
        if rule.target_field != field_name:
            continue
        if not rule_matches(rule, value):
            continue
        category = getattr(rule, "rule_category", None) or "general"
        if is_category_whitelisted(category, value, normalized):
            continue
        matched_entries.append(
            (
                rule,
                ContentSafetyMatchInfo(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    match_type=rule.match_type,
                    severity=rule.severity,
                    action=rule.action,
                ),
            )
        )

    if not matched_entries:
        return "allow", [], None

    matched = [info for _, info in matched_entries]
    decision = pick_final_decision(matched_entries)
    min_priority = min(rule.priority for rule, _ in matched_entries)
    candidates = [(rule, info) for rule, info in matched_entries if rule.priority == min_priority]
    top_rule, top = max(
        candidates,
        key=lambda pair: (
            ACTION_RANK.get(pair[1].action, 0),
            SEVERITY_RANK.get(pair[1].severity, 0),
        ),
    )
    category = getattr(top_rule, "rule_category", None) or "general"
    message = build_block_message(field_name, category)
    return decision, matched, message
