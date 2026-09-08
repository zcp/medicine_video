"""
Redis客户端工具 - 用户功能服务
从环境变量读取配置并提供异步Redis连接
"""
import redis.asyncio as redis
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
    # 推荐：直接用URL创建连接池
    redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
else:
    # 兼容没有URL时的传统写法
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    redis_pool = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True
    )


def get_redis_client() -> redis.Redis:
    """获取一个 Redis 客户端连接"""
    return redis.Redis(connection_pool=redis_pool)


async def test_redis_connection() -> bool:
    """测试Redis连接是否正常"""
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        logger.info("Redis连接测试成功")
        return True
    except Exception as e:
        logger.error(f"Redis连接测试失败: {e}")
        return False 