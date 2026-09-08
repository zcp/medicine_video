"""
手机号工具模块 —— 提供中国手机号格式校验与归一化能力

- 统一校验规则：^1[3-9]\\d{9}$
- 统一入库格式：纯 11 位（去除 +86/86 前缀、空格、横线）
- 所有涉及手机号明文入站的 Schema / Service / CRUD 统一引用本模块
"""
import re

CN_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def normalize_cn_phone(phone: str) -> str:
    """归一化手机号：去空白/横线、去 +86/86 前缀，返回纯 11 位"""
    value = str(phone or "").strip()
    value = value.replace(" ", "").replace("-", "")
    if value.startswith("+86"):
        value = value[3:]
    elif value.startswith("86") and len(value) == 13:
        value = value[2:]
    return value


def is_valid_cn_phone(phone: str) -> bool:
    """判断手机号是否合法（先归一化再匹配）"""
    return bool(CN_PHONE_PATTERN.fullmatch(normalize_cn_phone(phone)))


def validate_cn_phone(phone: str) -> str:
    """校验并返回归一化后的手机号；非法时抛 ValueError"""
    normalized = normalize_cn_phone(phone)
    if not CN_PHONE_PATTERN.fullmatch(normalized):
        raise ValueError("手机号格式不正确")
    return normalized
