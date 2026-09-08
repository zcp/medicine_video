"""政治敏感文本检测占位客户端（add-docs/13 §1.4）"""

import logging
import os
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class PoliticalTextProvider(str, Enum):
    PLACEHOLDER = "placeholder"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    NETEASE = "netease"


def _get_provider() -> PoliticalTextProvider:
    raw = os.getenv("POLITICAL_TEXT_PROVIDER", "placeholder").lower()
    try:
        return PoliticalTextProvider(raw)
    except ValueError:
        logger.warning("未知 POLITICAL_TEXT_PROVIDER=%s，回退 placeholder", raw)
        return PoliticalTextProvider.PLACEHOLDER


class PoliticalTextServiceError(Exception):
    """政治敏感 API 不可用"""


async def check_political_text(text: str, *, provider: Optional[PoliticalTextProvider] = None) -> bool:
    """
    返回 True 表示命中政治敏感（应 block）。
    PLACEHOLDER 默认返回 False；可通过 POLITICAL_TEXT_PLACEHOLDER_REJECT=true 联调 stub。
    非 placeholder 厂商未接密钥时抛 PoliticalTextServiceError → 写入型接口 2004。
    """
    provider = provider or _get_provider()

    if provider == PoliticalTextProvider.PLACEHOLDER:
        if os.getenv("POLITICAL_TEXT_PLACEHOLDER_REJECT", "false").lower() == "true":
            return True
        return False

    api_key = os.getenv("POLITICAL_TEXT_API_KEY", "")
    if not api_key:
        raise PoliticalTextServiceError("政治敏感 API 未配置密钥")

    logger.warning("政治敏感 API provider=%s 尚未实现，拒绝写入", provider.value)
    raise PoliticalTextServiceError(f"政治敏感 API provider={provider.value} 尚未实现")
