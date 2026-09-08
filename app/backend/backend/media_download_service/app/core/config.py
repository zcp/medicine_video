import os
from pathlib import Path
from typing import List
import logging
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings:
    """Application configuration class using standard Python features."""

    # --- Project Information ---
    PROJECT_NAME: str = "媒体下载服务"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # --- Security Configuration ---
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # --- Database Configuration (Read from environment) ---
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "media_download_test")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # --- Celery Configuration (Read from environment) ---
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # --- Download Configuration ---
    # Reads from the environment variable set by docker-compose
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", "D:\\storage"))
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    CONCURRENT_DOWNLOADS: int = 5

    # --- Logging Configuration ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = Path("logs")

    # ============ 爬虫配置 (Crawler Configuration) ============

    # 微赞爬虫配置
    VZAN_USERNAME: str = os.getenv("VZAN_USERNAME", "xxxx")
    VZAN_PASSWORD: str = os.getenv("VZAN_PASSWORD", "xxxx")
    VZAN_TOKEN: str = os.getenv("VZAN_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2IjoiNiIsInJvbCI6IjIsMTIiLCJhaWQiOiI0OWU3YTk0ZC0xN2NkLTQ4NTUtYjAxNC0wMzFmMThjMmIzODkiLCJ1aWQiOiIyMjM4NTA1MDkiLCJsaWQiOiIxMTc0OTU0OSIsImFwcGlkIjoiMTgiLCJ0eXBlIjoiMCIsIm5iZiI6MTc2MzUyOTI5MCwiZXhwIjoxNzYzNTcyNTIwLCJpYXQiOjE3NjM1MjkzMjAsImlzcyI6InZ6YW4iLCJhdWQiOiJ2emFuIn0.Z2hUq2dDNVjoaX23-y8dMBzIO47AgxozFI8L1StWf00")
    VZAN_COOKIE: str = os.getenv("VZAN_COOKIE","LivesId=006041a5-66e7-43d3-bff2-176521efd6eb; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22627117678128132096%22%2C%22first_id%22%3A%2219a8fd25178a99-02396169d767bc-26061b51-1821369-19a8fd251791b0a%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219a8fd25178a99-02396169d767bc-26061b51-1821369-19a8fd251791b0a%22%7D; Hm_lvt_29ea0df3279d9bf11c4ba5ff280126f3=1763349518,1763433130; HMACCOUNT=59D0425ABF362CBB; vzanuid=627117678128132096; UserEquipment=vzanChrome4wQDW637; Hm_lpvt_29ea0df3279d9bf11c4ba5ff280126f3=1763529170; fromtype=pc-www.vzan.com; UserCookieNew=49e7a94d-17cd-4855-b014-031f18c2b389; UserCookieToken=23c04a920f99127145965465d3062512; liveticket=5Li4cj/JZBdD91TrIhrAVuRi7WdPpR9tZbXgp7SiUwhpg6on7hdffjEcI9fZMkDHFnUctBKNuvTVuyrxYRgWeg==; _uetsid=1eb1cfe0c36411f0b254010c06ea35d5; _uetvid=1eb1fa20c36411f0a0e3df210e39057f")
    # 爬虫通用配置
    CRAWLER_TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "10"))
    CRAWLER_TEMP_DIR: str = os.getenv("CRAWLER_TEMP_DIR", "/tmp/vzan_crawler")
    CRAWLER_BATCH_SIZE: int = int(os.getenv("CRAWLER_BATCH_SIZE", "100"))

    # 集成配置
    CRAWL_IMPORT_AUTO_START: bool = os.getenv("CRAWL_IMPORT_AUTO_START", "false").lower() == "true"
    CRAWL_IMPORT_SKIP_DUPLICATES: bool = os.getenv("CRAWL_IMPORT_SKIP_DUPLICATES", "true").lower() == "true"
    CRAWL_IMPORT_DELETE_TEMP_FILE: bool = os.getenv("CRAWL_IMPORT_DELETE_TEMP_FILE", "true").lower() == "true"

    # Token加密密钥
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

    RUN_INTEGRATION_TESTS: int = int(os.getenv("RUN_INTEGRATION_TESTS", "1"))
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Constructs the asynchronous database connection URL."""
        # Note: For async, the driver is typically specified in the database.py engine creation
        #url = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        # url is from database.py
        url = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        logger.info(f"Database Connection URL: {url}")
        return url

    def __init__(self):
        logger.info("Configuration initialized.")
        # You can add post-init logic here if needed in the future


# Create a single, global instance of the settings
settings = Settings()