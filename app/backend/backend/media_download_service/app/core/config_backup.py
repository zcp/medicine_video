import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "媒体下载服务"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据库配置

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "media_download_test")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(" CELERY_RESULT_BACKEND", "redis://redis:6379/0")


    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # 下载配置
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", "D:\storage"))
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    CONCURRENT_DOWNLOADS: int = 5
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = Path("logs")

    @property
    def get_database_url(self) -> str:
        """获取数据库连接 URL"""
        url = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        logger.info(f"数据库连接 URL: {url}")
        return url

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SQLALCHEMY_DATABASE_URI = self.get_database_url
        logger.info("配置初始化完成")

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    class Config:
        case_sensitive = True
         #env_file = ".env.docker"

settings = Settings() 