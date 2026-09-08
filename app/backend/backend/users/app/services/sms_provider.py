"""
短信服务抽象层 —— SmsProvider

Phase 3: Mock 模式
- MockSmsProvider：开发环境，不真发短信，日志记录
- AliyunSmsProvider：生产环境，接入阿里云「短信认证」（号码认证服务 PNVS，SendSmsVerifyCode）
"""
import json
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
    """生产环境阿里云短信实现 —— 阿里云「短信认证」（免企业资质通道）

    接入号码认证服务 PNVS 的短信认证（API：SendSmsVerifyCode，产品 Dypnsapi 2017-05-25）。
    系统预置签名与验证码模板，个人实名即可开通；PhoneNumbers 要求纯 11 位
    （业务层已统一归一化，见 app/core/phone.py）。
    CodeType=1 自定义验证码：短信内容即我们 Redis 中的 OTP，核验仍走现有 Redis 闭环。
    """

    def __init__(self, access_key_id: str, access_key_secret: str,
                 sign_name: str, template_code: str):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code

    async def send(self, phone: str, code: str, template_params: dict = None) -> bool:
        # 懒加载 SDK：未安装时不阻塞服务启动，返回 False 由上层降级处理
        try:
            from alibabacloud_dypnsapi20170525.client import Client
            from alibabacloud_dypnsapi20170525 import models as dypns_models
            from alibabacloud_tea_openapi import models as open_api_models
        except ImportError:
            logger.warning(
                "[Aliyun SMS] alibabacloud-dypnsapi20170525 未安装，请执行: "
                "pip install alibabacloud-dypnsapi20170525"
            )
            return False

        try:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint="dypnsapi.aliyuncs.com",
            )
            client = Client(config)
            request = dypns_models.SendSmsVerifyCodeRequest(
                phone_number=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=json.dumps({"code": code}),
                code_type=1,
            )
            response = await client.send_sms_verify_code_async(request)
            body = response.body
            if body and body.code == "OK":
                logger.info(f"[Aliyun SMS] 发送成功: to={phone[:3]}****{phone[-4:]}")
                return True
            logger.warning(
                f"[Aliyun SMS] 发送失败: code={getattr(body, 'code', None)}, "
                f"message={getattr(body, 'message', None)}"
            )
            return False
        except Exception as e:
            logger.warning(f"[Aliyun SMS] 发送异常: {e}")
            return False

    async def health_check(self) -> bool:
        return False
