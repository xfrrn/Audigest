import asyncio
import os
from typing import Any

from loguru import logger
from sqlmodel import Session

from backend.core.config import settings
from backend.core.database import engine
from backend.core.utils import detect_language_from_title
from backend.models import SourceMedia
from backend.services.downloader import MediaDownloader
from backend.services.storage import StorageManager
from backend.services.summarizer import Summarizer
from backend.services.transcriber import AudioTranscriber

transcriber_mode = "cloud" if settings.DEEPGRAM_API_KEY else "local"

downloader = MediaDownloader()
transcriber = AudioTranscriber(
    mode=transcriber_mode,
    api_key=settings.DEEPGRAM_API_KEY,
    hf_token=settings.HF_TOKEN,
    device="cuda",
)
storage = StorageManager()
summarizer = Summarizer()


async def process_media_task(ctx: Any, media_id: int):
    """
    [Worker 核心任务] 全流程处理：下载 -> 转录 -> 存储 -> 总结
    被 ARQ 队列调用
    """
    logger.info(f"👷 [Worker] 接到任务: MediaID={media_id}")

    with Session(engine) as session:
        # 1. 获取任务信息
        media = session.get(SourceMedia, media_id)
        if not media:
            logger.error(f"❌ 任务不存在: MediaID={media_id}")
            return
        try:
            # 第一步：下载
            _update_status(session, media, "downloading")
            if media.local_audio_path and os.path.exists(media.local_audio_path):
                logger.info(f"⏭️ 文件已存在，跳过下载: {media.local_audio_path}")
            else:
                dl_result = await asyncio.to_thread(downloader.download, media.original_url, media.platform)

                media.title = dl_result["title"]
                media.author = dl_result["author"]
                media.duration = dl_result["duration"]
                media.local_audio_path = dl_result["local_path"]
                session.add(media)
                session.commit()

            # 第二步：转录
            _update_status(session, media, "transcribing")
            target_lang = detect_language_from_title(media.title)
            segments = await asyncio.to_thread(transcriber.transcribe, media.local_audio_path, language=target_lang)

            # 第三步：存储
            txt_path = storage.save_transcript(session, media.id, segments)

            # 第四步：总结
            _update_status(session, media, "summarizing")
            await asyncio.to_thread(summarizer.summarize_content, session, media.id, txt_path)
            _update_status(session, media, "completed")
            logger.success(f"🎉 [Worker] 任务 {media_id} 全部流程执行完毕！")

        except Exception as e:
            logger.exception(f"❌ [Worker] 任务 {media_id} 失败")
            media.status = "failed"
            media.error_msg = str(e)
            session.add(media)
            session.commit()


def _update_status(session: Session, media: SourceMedia, status: str):
    """辅助函数：更新状态并提交"""
    logger.info(f"🔄 [Status] {media.id}: {media.status} -> {status}")
    media.status = status
    session.add(media)
    session.commit()
    session.refresh(media)
