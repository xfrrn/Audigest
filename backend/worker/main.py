from loguru import logger

from backend.core.config import settings
from backend.core.database import init_db
from backend.core.queue import REDIS_SETTINGS
from backend.worker.tasks import process_media_task


async def startup(ctx):
    logger.info("👷 Worker 正在启动，检查数据库连接...")
    init_db()


def get_max_jobs():
    if settings.DEEPGRAM_API_KEY:
        return 5
    return 1


class WorkerSettings:
    """
    ARQ Worker 配置
    """

    functions = [process_media_task]
    redis_settings = REDIS_SETTINGS
    max_jobs = get_max_jobs()
    job_timeout = 3600
    on_startup = startup
