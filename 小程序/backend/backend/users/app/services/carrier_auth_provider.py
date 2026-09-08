"""
号码认证服务抽象层 —— CarrierAuthProvider

Phase 4: Mock 模式
- MockCarrierAuthProvider：开发环境，carrier_token 本身编码手机号
- AliyunCarrierAuthProvider：生产环境，调用阿里云号码认证 API（审核通过后实现）
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


class AliyunCarrierAuthProvider(CarrierAuthProvider):
    """生产环境阿里云号码认证实现 —— 骨架（审核通过后实现方法体）"""

    def __init__(self, access_key_id: str, access_key_secret: str):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    async def get_phone_number(self, carrier_token: str) -> str:
        # TODO: 接入阿里云号码认证 SDK
        # from alibabacloud_dypnsapi20170525.client import Client
        # request = models.GetMobileRequest(access_token=carrier_token)
        # response = client.get_mobile(request)
        # return response.body.mobile
        logger.warning("[Aliyun Carrier] Provider not implemented yet")
        raise NotImplementedError("阿里云号码认证服务尚未接入")

    async def health_check(self) -> bool:
        return False


class DCloudCarrierAuthProvider(CarrierAuthProvider):
    """DCloud univerify —— 手机号已由云函数解密，直接信任

    云函数 get-phone-number 已通过运营商 SDK 解密获取手机号，
    后端只需用该手机号进行注册或登录，无需再次调用号码认证 API。
    """

    async def get_phone_number(self, carrier_token: str) -> str:
        """carrier_token 就是云函数解密后的真实手机号"""
        # 兼容开发环境的 mock: 前缀（前端 mock 模式直接传手机号）
        if carrier_token.startswith("mock:"):
            phone = carrier_token.replace("mock:", "")
            logger.info(f"[DCloud Carrier] mock 模式解析手机号: phone={phone[:3]}****{phone[-4:]}")
            return phone
        logger.info(f"[DCloud Carrier] 接收云函数转发手机号: phone={carrier_token[:3]}****{carrier_token[-4:]}")
        return carrier_token

    async def health_check(self) -> bool:
        return True
