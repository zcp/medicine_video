"""
微信小程序登录换号抽象层 —— WeChatAuthProvider

- MockWeChatAuthProvider：开发环境，code 格式 mock:{openid}
- OfficialWeChatAuthProvider：生产环境，调用微信 jscode2session
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger("wechat_auth")

JSCODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _mask_openid(openid: str) -> str:
    if not openid:
        return ""
    if len(openid) <= 8:
        return openid[:2] + "****" + openid[-2:]
    return openid[:4] + "****" + openid[-4:]


class WeChatAuthProvider(ABC):
    """微信小程序 code → openid 抽象接口"""

    @abstractmethod
    async def exchange_code(self, code: str) -> str:
        """用 wx.login code 换取 openid，返回 openid 字符串"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查换号服务是否可用"""
        ...


class MockWeChatAuthProvider(WeChatAuthProvider):
    """开发环境 Mock —— code 直接编码 openid

    约定格式：code = "mock:{openid}"
    示例：code = "mock:oxMOCK_OPENID_001" → 返回 "oxMOCK_OPENID_001"
    """

    async def exchange_code(self, code: str) -> str:
        code = (code or "").strip()
        if not code.startswith("mock:"):
            raise ValueError("Mock code 格式错误，期望 mock:{openid}")
        openid = code[len("mock:"):].strip()
        if not openid:
            raise ValueError("Mock code 格式错误，openid 不能为空")
        logger.info(f"[MOCK WeChat] 解析 openid: {_mask_openid(openid)}")
        return openid

    async def health_check(self) -> bool:
        return True


class OfficialWeChatAuthProvider(WeChatAuthProvider):
    """正式环境：调用微信 jscode2session

    仅使用 openid；session_key / unionid 丢弃不落库。
    """

    def __init__(self, appid: str, secret: str, timeout: float = 5.0):
        self.appid = appid
        self.secret = secret
        self.timeout = timeout

    async def exchange_code(self, code: str) -> str:
        code = (code or "").strip()
        if not code:
            raise ValueError("微信 code 不能为空")

        params = {
            "appid": self.appid,
            "secret": self.secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(JSCODE2SESSION_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"[Official WeChat] jscode2session HTTP 失败: {e}")
            raise ValueError("微信登录失败，请重试") from e
        except Exception as e:
            logger.warning(f"[Official WeChat] jscode2session 解析失败: {e}")
            raise ValueError("微信登录失败，请重试") from e

        errcode = data.get("errcode", 0)
        if errcode not in (0, None):
            # 禁止回传微信 errmsg（可能含敏感配置信息）
            logger.warning(
                f"[Official WeChat] jscode2session 业务失败: errcode={errcode}"
            )
            raise ValueError("微信登录失败，请重试")

        openid: Optional[str] = data.get("openid")
        if not openid:
            logger.warning("[Official WeChat] 响应缺少 openid")
            raise ValueError("微信登录失败，请重试")

        logger.info(f"[Official WeChat] 换号成功: openid={_mask_openid(openid)}")
        return openid

    async def health_check(self) -> bool:
        return bool(self.appid and self.secret)
