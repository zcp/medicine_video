"""
认证相关的 Pydantic Schema 定义
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VerificationCodeRequest(BaseModel):
    """发送验证码请求模型"""
    channel: str = Field(..., description="发送渠道: EMAIL, SMS")
    recipient: str = Field(..., description="接收者: 邮箱或手机号")
    scenario: str = Field(..., description="使用场景: REGISTER, RESET_PASSWORD, LOGIN")
    captcha_id: Optional[str] = Field(None, description="图形验证码ID（LOGIN 场景可选）")
    captcha_solution: Optional[str] = Field(None, description="图形验证码答案（LOGIN 场景可选）")


class LoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="手机号/邮箱/用户名")
    password: str = Field(..., description="密码")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class PhoneLoginRequest(BaseModel):
    """手机号验证码登录请求模型"""
    login_ticket: str = Field(..., description="LOGIN 场景的 ticket（由 /verification-codes/verify 签发）")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class EmailLoginRequest(BaseModel):
    """邮箱验证码登录请求模型（V5）"""
    login_ticket: str = Field(..., description="LOGIN 场景的 ticket（channel=EMAIL，由 /verification-codes/verify 签发）")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: str = Field(..., description="用户邮箱")
    captcha_id: str = Field(..., description="图形验证码ID")
    captcha_solution: str = Field(..., description="图形验证码答案")


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认模型（支持邮箱 reset_token 与 OTP 验证后的 reset_ticket）"""
    reset_token: Optional[str] = Field(None, description="重置令牌（邮箱方式）")
    reset_ticket: Optional[str] = Field(None, description="重置票据（OTP 验证方式）")
    new_password: str = Field(..., min_length=8, description="新密码")


class VerifyCodeRequest(BaseModel):
    """校验验证码请求模型"""
    channel: str = Field(..., description="发送渠道: EMAIL, SMS")
    recipient: str = Field(..., description="接收者: 邮箱或手机号")
    scenario: str = Field(..., description="使用场景: RESET_PASSWORD, REGISTER, BIND_PHONE")
    code: str = Field(..., min_length=4, max_length=6, description="用户输入的验证码")


class SSOLoginRequest(BaseModel):
    """SSO登录请求模型"""
    id_token: str = Field(..., description="Authing ID Token")


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求模型（Phase 3：基于 ticket）"""
    register_ticket: str = Field(..., description="REGISTER 场景的 ticket（由 /verification-codes/verify 签发）")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class OneTapLoginRequest(BaseModel):
    """一键登录请求模型（Phase 4）"""
    carrier_token: str = Field(..., description="运营商 SDK 返回的临时 token")
    provider: str = Field(default="aliyun", description="号码认证提供商")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class CloudFunctionLoginRequest(BaseModel):
    """云函数签名一键登录请求模型（Phase 4 安全方案B — HMAC签名验证）

    客户端从云函数拿到 {phoneNumber, sign, timestamp} 后，
    直接提交给后端。后端通过 HMAC 验签确保手机号未被篡改。
    """
    phone: str = Field(..., description="云函数解密后的真实手机号")
    sign: str = Field(..., description="HMAC-SHA256(phone+timestamp, PSK) 签名")
    timestamp: str = Field(..., description="签名时间戳（毫秒）")
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )


class WeChatLoginRequest(BaseModel):
    """微信小程序一键授权登录请求（V4）"""
    code: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="wx.login 返回的 code；Mock 模式为 mock:{openid}",
    )
    agreed_to_terms: bool = Field(
        default=False,
        description="用户是否同意服务条款和隐私政策；须为 true",
    )

    @field_validator("code")
    @classmethod
    def strip_code(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("code 不能为空")
        return v
 
