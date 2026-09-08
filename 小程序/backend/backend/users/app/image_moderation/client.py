"""图片内容审核占位客户端（add-docs/12 §1.4.6）

V1.0：IMAGE_MODERATION_PROVIDER=placeholder 时不发起外网请求、不做内容检测，始终放行。
生产切换 WECHAT / ALIYUN / TENCENT 后在此对接真实 API。
"""

import logging
import os
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ImageModerationProvider(str, Enum):
    PLACEHOLDER = "placeholder"  # 默认：开发联调，不检测，始终 pass
    WECHAT = "wechat"            # 微信开放平台 / 小程序内容安全
    ALIYUN = "aliyun"            # 阿里云内容安全
    TENCENT = "tencent"          # 腾讯云图片内容安全


class ImageModerationResult(BaseModel):
    passed: bool
    label: Optional[str] = None
    provider: ImageModerationProvider
    raw_response: Optional[dict] = None


class ImageModerationServiceError(Exception):
    """图片审核服务不可用（写入型接口应拒绝，见文档 422/2004）"""


def _resolve_provider() -> ImageModerationProvider:
    raw = os.getenv("IMAGE_MODERATION_PROVIDER", "placeholder").lower()
    try:
        return ImageModerationProvider(raw)
    except ValueError:
        logger.warning("未知 IMAGE_MODERATION_PROVIDER=%s，回退 placeholder", raw)
        return ImageModerationProvider.PLACEHOLDER


class ImageModerationClient:
    """图片内容审核统一入口"""

    def __init__(self, provider: Optional[ImageModerationProvider] = None):
        self.provider = provider or _resolve_provider()

    async def moderate(
        self,
        *,
        file_bytes: bytes,
        content_type: str,
        scene: Literal["avatar"] = "avatar",
    ) -> ImageModerationResult:
        """
        落盘前调用。placeholder 模式不检测，直接返回 passed=True。
        真实厂商对接后：违规 → passed=False；服务故障 → 抛 ImageModerationServiceError。
        """
        if self.provider == ImageModerationProvider.PLACEHOLDER:
            logger.debug("图片审核占位模式：scene=%s，跳过检测", scene)
            return ImageModerationResult(passed=True, provider=self.provider)

        return await self._call_vendor_api(
            file_bytes=file_bytes,
            content_type=content_type,
            scene=scene,
        )

    async def _call_vendor_api(
        self,
        *,
        file_bytes: bytes,
        content_type: str,
        scene: Literal["avatar"],
    ) -> ImageModerationResult:
        """第三方图片审核 API（V1.0 仅占位，签约厂商后实现）"""
        api_key = os.getenv("IMAGE_MODERATION_API_KEY", "")
        if not api_key:
            raise ImageModerationServiceError("图片审核 API 未配置密钥")

        if self.provider == ImageModerationProvider.WECHAT:
            # TODO: 对接微信 mediaCheckAsync / imgSecCheck 等
            raise ImageModerationServiceError("微信图片审核尚未对接")

        if self.provider == ImageModerationProvider.ALIYUN:
            # TODO: 对接阿里云图片审核
            raise ImageModerationServiceError("阿里云图片审核尚未对接")

        if self.provider == ImageModerationProvider.TENCENT:
            # TODO: 对接腾讯云图片审核
            raise ImageModerationServiceError("腾讯云图片审核尚未对接")

        raise ImageModerationServiceError(f"不支持的图片审核 provider={self.provider.value}")
