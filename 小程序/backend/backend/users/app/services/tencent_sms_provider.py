"""
腾讯云短信服务 —— TencentCloudSmsProvider

实现 SmsProvider 抽象接口，通过腾讯云短信 SDK 发送验证码。
"""
import logging
import json
from typing import Optional

from app.services.sms_provider import SmsProvider

logger = logging.getLogger("sms")


class TencentCloudSmsProvider(SmsProvider):
    """腾讯云短信实现 —— 调用腾讯云短信 API"""

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        sdk_app_id: str,
        sign_name: str,
        template_code: str,
    ):
        """
        Args:
            secret_id: 腾讯云 API 密钥 ID（从控制台获取）
            secret_key: 腾讯云 API 密钥 Key
            sdk_app_id: 短信 SDK App ID（从短信控制台获取）
            sign_name: 短信签名（需在腾讯云短信控制台审核通过）
            template_code: 短信模板 ID（需在腾讯云短信控制台审核通过）
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.sdk_app_id = sdk_app_id
        self.sign_name = sign_name
        self.template_code = template_code

    async def send(
        self,
        phone: str,
        code: str,
        template_params: Optional[dict] = None,
    ) -> bool:
        """
        通过腾讯云短信 SDK 发送验证码

        Args:
            phone: 目标手机号（如 +8613800138000）
            code: 验证码内容
            template_params: 模板参数，默认使用验证码模板

        Returns:
            bool: 是否发送成功
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
                TencentCloudSDKException,
            )
            from tencentcloud.sms.v20210111 import sms_client, models

            # 1. 实例化认证对象
            cred = credential.Credential(self.secret_id, self.secret_key)

            # 2. 实例化短信客户端
            client = sms_client.SmsClient(cred, "ap-guangzhou")

            # 3. 组装请求
            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.sdk_app_id
            req.SignName = self.sign_name
            req.TemplateId = self.template_code

            # 模板参数：第一个参数为验证码，第二个参数为有效期（分钟）
            minutes = "5"
            if template_params and "minutes" in template_params:
                minutes = str(template_params["minutes"])
            req.TemplateParamSet = [code, minutes]

            # 手机号格式：+86 前缀
            req.PhoneNumberSet = [phone]

            # 4. 发送
            resp = client.SendSms(req)

            # 5. 检查发送结果
            send_status = resp.SendStatusSet or []
            for status in send_status:
                if status.Code == "Ok":
                    logger.info(
                        f"[Tencent SMS] 发送成功: phone={phone[:3]}****{phone[-4:]}, "
                        f"code_length={len(code)}"
                    )
                    return True
                else:
                    logger.warning(
                        f"[Tencent SMS] 发送失败: phone={phone[:3]}****{phone[-4:]}, "
                        f"code={status.Code}, message={status.Message}"
                    )
                    return False

            logger.warning("[Tencent SMS] 发送返回为空")
            return False

        except TencentCloudSDKException as e:
            logger.error(f"[Tencent SMS] SDK 调用异常: {e}")
            return False
        except ImportError:
            logger.error(
                "[Tencent SMS] tencentcloud-sdk-python 未安装，请执行: "
                "pip install tencentcloud-sdk-python"
            )
            return False
        except Exception as e:
            logger.error(f"[Tencent SMS] 发送异常: {e}")
            return False

    async def health_check(self) -> bool:
        """检查腾讯云短信服务是否可用（基础配置完整性检查）"""
        if not all([self.secret_id, self.secret_key, self.sdk_app_id,
                     self.sign_name, self.template_code]):
            logger.warning("[Tencent SMS] 配置不完整，无法使用")
            return False
        return True
