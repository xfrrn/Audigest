# src/core/queue.py
from arq.connections import ArqRedis, RedisSettings, create_pool

from backend.core.config import settings

# 1. 定义配置
REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)


async def get_redis_pool() -> ArqRedis:
    """
    创建并返回一个 Redis 连接池
    用于 API 层推送任务
    """
    return await create_pool(REDIS_SETTINGS)
