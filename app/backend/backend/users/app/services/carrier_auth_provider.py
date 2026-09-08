"""
号码认证服务抽象层 —— CarrierAuthProvider

Phase 4: Mock 模式
- MockCarrierAuthProvider：开发环境，carrier_token 本身编码手机号
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("carrier_auth")


class CarrierAuthProvider(ABC):
    """号码认证服务抽象接口"""

    @abstractmethod
    async def get_phone_number(self, carrier_token: str) -> str:
        """通过运营商 token 换取真实手机号，返回手机号字符串"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查号码认证服务是否可用"""
        ...


class MockCarrierAuthProvider(CarrierAuthProvider):
    """开发环境 Mock —— carrier_token 直接编码手机号

    约定格式：token = "mock:{phone}"
    示例：token = "mock:+8613800138000" → 返回 "+8613800138000"
    """

    async def get_phone_number(self, carrier_token: str) -> str:
        if carrier_token.startswith("mock:"):
            phone = carrier_token.replace("mock:", "")
            logger.info(f"[MOCK Carrier] 解析手机号: phone={phone[:3]}****{phone[-4:]}")
            return phone
        raise ValueError("Mock token 格式错误，期望 mock:{phone}")

    async def health_check(self) -> bool:
        return True
