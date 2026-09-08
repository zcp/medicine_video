"""
Users Service - Application Configuration

配置管理模块
"""

import os
import warnings
from typing import List


class Settings:
    """应用配置类"""
    
    # 环境标识
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # 项目基本信息
    PROJECT_NAME: str = "Users Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "用户服务API"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    # ⚠️ 生产环境必须设置此环境变量，不允许使用默认值
    # 开发环境：如果未设置，使用空字符串，验证逻辑会给出警告但不阻止启动
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "users_service_test")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        """异步数据库连接URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """同步数据库连接URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # CORS配置
    # 从环境变量读取，支持逗号分隔的多个域名
    # 格式: "http://localhost:5174,https://example.com"
    _CORS_ORIGINS_STR: str = os.getenv("CORS_ORIGINS", "*")
    
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """CORS允许的源列表"""
        return [
            origin.strip() 
            for origin in self._CORS_ORIGINS_STR.split(",") 
            if origin.strip()
        ]
    
    # JWT配置
    # ⚠️ 生产环境必须设置此环境变量，不允许使用默认值
    # 开发环境：如果未设置，使用空字符串，验证逻辑会给出警告但不阻止启动
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    # 允许 iat/exp 时钟偏差（秒）；缓解 Docker/宿主机时钟漂移导致的 iat 未生效
    JWT_LEEWAY_SECONDS: int = int(os.getenv("JWT_LEEWAY_SECONDS", "60"))

    # 服务间内部令牌（live_core 同步头像等）
    INTERNAL_SERVICE_TOKEN: str = os.getenv("INTERNAL_SERVICE_TOKEN", "")

    # 16-D2：注销后 best-effort 调 live_core 清私货
    LIVE_CORE_SERVICE_URL: str = os.getenv(
        "LIVE_CORE_SERVICE_URL", "http://live_core_service:8000"
    )
    LIVE_CORE_CLEANUP_TIMEOUT_SECONDS: float = float(
        os.getenv("LIVE_CORE_CLEANUP_TIMEOUT_SECONDS", "5")
    )    
    # Authing配置（可选）
    VITE_CLIENT_ID: str = os.getenv("VITE_CLIENT_ID", "")
    USER_POOL_SECRET: str = os.getenv("USER_POOL_SECRET", "")
    APP_HOST: str = os.getenv("APP_HOST", "")
    REDIRECT_URL: str = os.getenv("REDIRECT_URL", "")
    ISSUER: str = os.getenv("ISSUER", "")

    # Verification / carrier provider configuration
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "mock").lower()
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "mock").lower()
    CARRIER_AUTH_PROVIDER: str = os.getenv("CARRIER_AUTH_PROVIDER", "mock").lower()
    ALIYUN_ACCESS_KEY_ID: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_SMS_SIGN_NAME: str = os.getenv("ALIYUN_SMS_SIGN_NAME", "")
    ALIYUN_SMS_TEMPLATE_CODE: str = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "")
    
    # DCloud 云函数 API 密钥（用于云函数直调后端的身份验证）
    DCLOUD_API_KEY: str = os.getenv("DCLOUD_API_KEY", "")

    # 微信小程序一键授权登录（V4）
    WECHAT_AUTH_PROVIDER: str = os.getenv("WECHAT_AUTH_PROVIDER", "mock").lower()
    WECHAT_MINI_APPID: str = os.getenv("WECHAT_MINI_APPID", "")
    WECHAT_MINI_SECRET: str = os.getenv("WECHAT_MINI_SECRET", "")
    
    # 腾讯云短信配置
    TENCENT_SECRET_ID: str = os.getenv("TENCENT_SECRET_ID", "")
    TENCENT_SECRET_KEY: str = os.getenv("TENCENT_SECRET_KEY", "")
    TENCENT_SMS_APP_ID: str = os.getenv("TENCENT_SMS_APP_ID", "")
    TENCENT_SMS_SIGN_NAME: str = os.getenv("TENCENT_SMS_SIGN_NAME", "")
    TENCENT_SMS_TEMPLATE_CODE: str = os.getenv("TENCENT_SMS_TEMPLATE_CODE", "")

    # SMTP 邮件（EMAIL_PROVIDER=smtp 时填写，如 QQ 邮箱）
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "")
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    def __init__(self):
        """初始化配置并验证"""
        # 重新读取运行时可被 monkeypatch 覆盖的环境变量
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", self.ENVIRONMENT)
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", self.JWT_SECRET_KEY)
        self.JWT_LEEWAY_SECONDS = int(
            os.getenv("JWT_LEEWAY_SECONDS", str(self.JWT_LEEWAY_SECONDS))
        )
        self._CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", self._CORS_ORIGINS_STR)
        self.DEBUG = os.getenv("DEBUG", str(self.DEBUG)).lower() == "true"
        self.SMS_PROVIDER = os.getenv("SMS_PROVIDER", self.SMS_PROVIDER).lower()
        self.EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", self.EMAIL_PROVIDER).lower()
        self.CARRIER_AUTH_PROVIDER = os.getenv("CARRIER_AUTH_PROVIDER", self.CARRIER_AUTH_PROVIDER).lower()
        self.WECHAT_AUTH_PROVIDER = os.getenv("WECHAT_AUTH_PROVIDER", self.WECHAT_AUTH_PROVIDER).lower()
        self.WECHAT_MINI_APPID = os.getenv("WECHAT_MINI_APPID", self.WECHAT_MINI_APPID)
        self.WECHAT_MINI_SECRET = os.getenv("WECHAT_MINI_SECRET", self.WECHAT_MINI_SECRET)
        self.ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", self.ALIYUN_ACCESS_KEY_ID)
        self.ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", self.ALIYUN_ACCESS_KEY_SECRET)
        self.ALIYUN_SMS_SIGN_NAME = os.getenv("ALIYUN_SMS_SIGN_NAME", self.ALIYUN_SMS_SIGN_NAME)
        self.ALIYUN_SMS_TEMPLATE_CODE = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", self.ALIYUN_SMS_TEMPLATE_CODE)
        self.DCLOUD_API_KEY = os.getenv("DCLOUD_API_KEY", self.DCLOUD_API_KEY)
        self.TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", self.TENCENT_SECRET_ID)
        self.TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", self.TENCENT_SECRET_KEY)
        self.TENCENT_SMS_APP_ID = os.getenv("TENCENT_SMS_APP_ID", self.TENCENT_SMS_APP_ID)
        self.TENCENT_SMS_SIGN_NAME = os.getenv("TENCENT_SMS_SIGN_NAME", self.TENCENT_SMS_SIGN_NAME)
        self.TENCENT_SMS_TEMPLATE_CODE = os.getenv("TENCENT_SMS_TEMPLATE_CODE", self.TENCENT_SMS_TEMPLATE_CODE)
        self.SMTP_HOST = os.getenv("SMTP_HOST", self.SMTP_HOST)
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", str(self.SMTP_PORT)))
        self.SMTP_USER = os.getenv("SMTP_USER", self.SMTP_USER)
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", self.SMTP_PASSWORD)
        self.SMTP_FROM = os.getenv("SMTP_FROM", self.SMTP_FROM)
        self.SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", self.SMTP_FROM_NAME)
        # 根据环境决定验证严格程度
        if self.ENVIRONMENT == "production":
            self._validate_production_config()
        else:
            self._validate_development_config()
    
    def _validate_production_config(self):
        """生产环境严格验证"""
        errors = []
        
        # 验证数据库配置
        if not self.POSTGRES_PASSWORD:
            errors.append("❌ POSTGRES_PASSWORD 环境变量未设置")
        
        # 验证JWT配置
        if not self.JWT_SECRET_KEY:
            errors.append("❌ JWT_SECRET_KEY 环境变量未设置")
        elif len(self.JWT_SECRET_KEY) < 32:
            errors.append(f"❌ JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}）")
        
        # 验证CORS配置
        if "*" in self.BACKEND_CORS_ORIGINS:
            errors.append("❌ 生产环境CORS不允许使用 '*'，必须指定具体域名")
        
        # 验证DEBUG模式
        if self.DEBUG:
            errors.append("❌ 生产环境必须关闭DEBUG模式（设置 DEBUG=false）")

        if self.SMS_PROVIDER not in ("mock", "aliyun", "tencent"):
            errors.append("❌ SMS_PROVIDER 必须是 mock、aliyun 或 tencent")
        if self.EMAIL_PROVIDER not in ("mock", "smtp"):
            errors.append("❌ EMAIL_PROVIDER 必须是 mock 或 smtp")
        if self.CARRIER_AUTH_PROVIDER not in ("mock", "aliyun", "dcloud"):
            errors.append("❌ CARRIER_AUTH_PROVIDER 必须是 mock、aliyun 或 dcloud")
        if self.WECHAT_AUTH_PROVIDER not in ("mock", "official"):
            errors.append("❌ WECHAT_AUTH_PROVIDER 必须是 mock 或 official")

        if self.SMS_PROVIDER == "mock":
            errors.append("❌ 生产环境 SMS_PROVIDER 不允许使用 mock")
        if self.EMAIL_PROVIDER == "mock":
            errors.append("❌ 生产环境 EMAIL_PROVIDER 不允许使用 mock")
        if self.CARRIER_AUTH_PROVIDER == "mock":
            errors.append("❌ 生产环境 CARRIER_AUTH_PROVIDER 不允许使用 mock")
        if self.WECHAT_AUTH_PROVIDER == "mock":
            errors.append("❌ 生产环境 WECHAT_AUTH_PROVIDER 不允许使用 mock")

        if self.WECHAT_AUTH_PROVIDER == "official":
            if not self.WECHAT_MINI_APPID:
                errors.append("❌ WECHAT_MINI_APPID 环境变量未设置")
            if not self.WECHAT_MINI_SECRET:
                errors.append("❌ WECHAT_MINI_SECRET 环境变量未设置")

        if self.SMS_PROVIDER == "aliyun":
            if not self.ALIYUN_ACCESS_KEY_ID:
                errors.append("❌ ALIYUN_ACCESS_KEY_ID 环境变量未设置")
            if not self.ALIYUN_ACCESS_KEY_SECRET:
                errors.append("❌ ALIYUN_ACCESS_KEY_SECRET 环境变量未设置")
            if not self.ALIYUN_SMS_SIGN_NAME:
                errors.append("❌ ALIYUN_SMS_SIGN_NAME 环境变量未设置")
            if not self.ALIYUN_SMS_TEMPLATE_CODE:
                errors.append("❌ ALIYUN_SMS_TEMPLATE_CODE 环境变量未设置")

        if self.SMS_PROVIDER == "tencent":
            if not self.TENCENT_SECRET_ID:
                errors.append("❌ TENCENT_SECRET_ID 环境变量未设置")
            if not self.TENCENT_SECRET_KEY:
                errors.append("❌ TENCENT_SECRET_KEY 环境变量未设置")
            if not self.TENCENT_SMS_APP_ID:
                errors.append("❌ TENCENT_SMS_APP_ID 环境变量未设置")
            if not self.TENCENT_SMS_SIGN_NAME:
                errors.append("❌ TENCENT_SMS_SIGN_NAME 环境变量未设置")
            if not self.TENCENT_SMS_TEMPLATE_CODE:
                errors.append("❌ TENCENT_SMS_TEMPLATE_CODE 环境变量未设置")

        if self.CARRIER_AUTH_PROVIDER == "aliyun":
            if not self.ALIYUN_ACCESS_KEY_ID:
                errors.append("❌ ALIYUN_ACCESS_KEY_ID 环境变量未设置")
            if not self.ALIYUN_ACCESS_KEY_SECRET:
                errors.append("❌ ALIYUN_ACCESS_KEY_SECRET 环境变量未设置")

        if self.EMAIL_PROVIDER == "smtp":
            if not self.SMTP_HOST:
                errors.append("❌ SMTP_HOST 环境变量未设置")
            if not self.SMTP_USER:
                errors.append("❌ SMTP_USER 环境变量未设置")
            if not self.SMTP_PASSWORD:
                errors.append("❌ SMTP_PASSWORD 环境变量未设置")
        
        if errors:
            raise ValueError(
                "\n\n" + "="*60 + "\n" +
                "生产环境配置验证失败：\n" + 
                "\n".join(errors) +
                "\n" + "="*60 + "\n"
            )
    
    def _validate_development_config(self):
        """开发环境基础验证（使用警告而非错误）"""
        warnings_list = []
        
        if not self.POSTGRES_PASSWORD:
            warnings_list.append("⚠️  POSTGRES_PASSWORD 未设置，数据库连接可能失败")
            warnings_list.append("    💡 提示：请复制 .env.example 为 .env 并填写配置")
        
        if not self.JWT_SECRET_KEY:
            warnings_list.append("⚠️  JWT_SECRET_KEY 未设置，JWT认证将无法工作")
            warnings_list.append("    💡 提示：运行 'openssl rand -hex 32' 生成密钥")
        elif len(self.JWT_SECRET_KEY) < 32:
            warnings_list.append(f"⚠️  JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}），建议使用更长的密钥")

        if self.SMS_PROVIDER not in ("mock", "aliyun", "tencent"):
            warnings_list.append("⚠️  SMS_PROVIDER 必须是 mock、aliyun 或 tencent")
        if self.EMAIL_PROVIDER not in ("mock", "smtp"):
            warnings_list.append("⚠️  EMAIL_PROVIDER 必须是 mock 或 smtp")
        if self.EMAIL_PROVIDER == "smtp" and not self.SMTP_PASSWORD:
            warnings_list.append("⚠️  EMAIL_PROVIDER=smtp 但 SMTP_PASSWORD 未设置，邮件将无法发送")
        if self.CARRIER_AUTH_PROVIDER not in ("mock", "aliyun", "dcloud"):
            warnings_list.append("⚠️  CARRIER_AUTH_PROVIDER 必须是 mock、aliyun 或 dcloud")
        if self.WECHAT_AUTH_PROVIDER not in ("mock", "official"):
            warnings_list.append("⚠️  WECHAT_AUTH_PROVIDER 必须是 mock 或 official")
        if self.WECHAT_AUTH_PROVIDER == "official":
            if not self.WECHAT_MINI_APPID:
                warnings_list.append("⚠️  WECHAT_AUTH_PROVIDER=official 但 WECHAT_MINI_APPID 未设置")
            if not self.WECHAT_MINI_SECRET:
                warnings_list.append("⚠️  WECHAT_AUTH_PROVIDER=official 但 WECHAT_MINI_SECRET 未设置")
        
        if warnings_list:
            first_run_hint = ""
            if not self.POSTGRES_PASSWORD or not self.JWT_SECRET_KEY:
                first_run_hint = "\n\n💡 首次运行？请执行:\n   1. cp .env.example .env\n   2. 编辑 .env 文件填写配置\n"
            
            warning_message = (
                "\n" + "="*60 + 
                "\n⚠️  开发环境配置警告：\n" + 
                "\n".join(warnings_list) + 
                first_run_hint +
                "="*60
            )
            warnings.warn(warning_message, UserWarning)


# 创建全局配置实例
settings = Settings()
