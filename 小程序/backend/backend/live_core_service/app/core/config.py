"""
LiveCore Service - Application Configuration

配置管理模块
"""

import os
from typing import List, Optional
import warnings


class Settings:
    """应用配置类"""
    
    # 环境标识
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # 项目基本信息
    PROJECT_NAME: str = "LiveCore Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "直播核心功能服务API"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    # ⚠️ 生产环境必须设置此环境变量，不允许使用默认值
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "live_core_test")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Celery配置
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

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
    # 格式: "http://localhost:5175,https://example.com"
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
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # 开播门禁：ADMIN/SUPERADMIN 是否可旁路 can_stream（便于运营自测）
    ADMIN_STREAM_BYPASS: bool = os.getenv("ADMIN_STREAM_BYPASS", "true").lower() == "true"

    # 跨服务：专家头像同步到 users.avatar_url（方案 A）
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://users:8000")
    INTERNAL_SERVICE_TOKEN: str = os.getenv("INTERNAL_SERVICE_TOKEN", "")
    
    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 文件上传配置
    ROOM_MEDIA_ROOT_PATH: str = os.getenv("ROOM_MEDIA_ROOT_PATH", "./media")
    UPLOAD_MAX_SIZE: int = int(os.getenv("UPLOAD_MAX_SIZE", "10485760"))
    UPLOAD_ALLOWED_EXTENSIONS: str = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif")
    
    # 视频回放配置
    PLAYBACK_BASE_URL: str = os.getenv("PLAYBACK_BASE_URL", "http://localhost:8000")

    def __init__(self):
        """初始化配置并验证"""
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
        elif self.POSTGRES_PASSWORD == "324zq999":
            errors.append("❌ 生产环境不允许使用默认数据库密码 '324zq999'")
        
        # 验证JWT配置
        if not self.JWT_SECRET_KEY:
            errors.append("❌ JWT_SECRET_KEY 环境变量未设置")
        elif self.JWT_SECRET_KEY == "my-key":
            errors.append("❌ 生产环境不允许使用默认JWT密钥 'my-key'")
        elif len(self.JWT_SECRET_KEY) < 32:
            errors.append(f"❌ JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}）")
        
        # 验证CORS配置
        if "*" in self.BACKEND_CORS_ORIGINS:
            errors.append("❌ 生产环境CORS不允许使用 '*'，必须指定具体域名")
        
        # 验证DEBUG模式
        if self.DEBUG:
            errors.append("❌ 生产环境必须关闭DEBUG模式（设置 DEBUG=false）")
        
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
        elif self.POSTGRES_PASSWORD == "324zq999":
            warnings_list.append("⚠️  使用默认数据库密码 '324zq999'，建议在 .env 文件中设置自定义密码")
        
        if not self.JWT_SECRET_KEY:
            warnings_list.append("⚠️  JWT_SECRET_KEY 未设置，JWT认证将无法工作")
            warnings_list.append("    💡 提示：运行 'openssl rand -hex 32' 生成密钥")
        elif self.JWT_SECRET_KEY == "my-key":
            warnings_list.append("⚠️  使用默认JWT密钥 'my-key'，建议在 .env 文件中设置自定义密钥")
        elif len(self.JWT_SECRET_KEY) < 32:
            warnings_list.append(f"⚠️  JWT_SECRET_KEY 长度不足32个字符（当前：{len(self.JWT_SECRET_KEY)}），建议使用更长的密钥")
        
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