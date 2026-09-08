"""
短信服务抽象层 —— SmsProvider

Phase 3: Mock 模式
- MockSmsProvider：开发环境，不真发短信，日志记录
- AliyunSmsProvider：生产环境，调用阿里云短信 API（审核通过后实现）
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("sms")


class SmsProvider(ABC):
    """短信服务抽象接口"""

    @abstractmethod
    async def send(self, phone: str, code: str, template_params: dict = None) -> bool:
        """发送短信验证码，返回是否成功"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查短信服务是否可用"""
        ...


class MockSmsProvider(SmsProvider):
    """开发环境 Mock —— 不真发短信，日志记录"""

    async def send(self, phone: str, code: str, template_params: dict = None) -> bool:
        # 只打掩码信息，不打 code 明文
        logger.debug(
            f"[MOCK SMS] to={phone[:3]}****{phone[-4:]} "
            f"code_length={len(code)}"
        )
        return True

    async def health_check(self) -> bool:
        return True


class AliyunSmsProvider(SmsProvider):
    """生产环境阿里云短信实现 —— 骨架（审核通过后实现 send 方法体）"""

    def __init__(self, access_key_id: str, access_key_secret: str,
                 sign_name: str, template_code: str):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code

    async def send(self, phone: str, code: str, template_params: dict = None) -> bool:
        # TODO: 接入阿里云短信 SDK
        # from alibabacloud_dysmsapi20170525.client import Client
        # from alibabacloud_tea_openapi import models as open_api_models
        # from alibabacloud_dysmsapi20170525 import models as sms_models
        # ... 实现发送逻辑
        logger.warning("[Aliyun SMS] Provider not implemented yet")
        return False

    async def health_check(self) -> bool:
        return False
