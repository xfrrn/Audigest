from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session, select

from backend.api.schemas import (
    MediaCreateRequest,
    MediaResponse,
    SummaryResponse,
    TranscriptResponse,
)
from backend.core.database import get_session
from backend.core.queue import get_redis_pool
from backend.models import SourceMedia, Summary, TranscriptSegment
from backend.services.url_parser import URLParser

router = APIRouter()


@router.post("/media/", response_model=MediaResponse)
async def create_media_task(request: MediaCreateRequest, session: Session = Depends(get_session)):
    """
    提交 URL -> 清洗 -> 查重 -> 入库 -> 推送 Redis 队列
    """
    clean_url = URLParser.clean_url(str(request.url))
    platform = URLParser.detect_platform(clean_url)

    statement = select(SourceMedia).where(SourceMedia.original_url == clean_url)
    existing_media = session.exec(statement).first()

    if existing_media:
        if existing_media.status == "failed":
            existing_media.status = "pending"
            existing_media.error_msg = None
            session.add(existing_media)
            session.commit()
            session.refresh(existing_media)
        else:
            return existing_media
    else:
        existing_media = SourceMedia(
            original_url=clean_url,
            platform=platform,
            title="获取中...",
            status="pending",
        )
        session.add(existing_media)
        session.commit()
        session.refresh(existing_media)

    try:
        redis = await get_redis_pool()
        await redis.enqueue_job("process_media_task", existing_media.id)
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接失败: {e}")

    return existing_media


@router.get("/media/", response_model=List[MediaResponse])
def get_media_list(skip: int = 0, limit: int = 20, session: Session = Depends(get_session)):
    """
    获取任务列表 (只返回基础信息，不含逐字稿)
    """
    statement = select(SourceMedia).order_by(SourceMedia.created_at.desc()).offset(skip).limit(limit)
    results = session.exec(statement).all()
    return results


@router.get("/media/{media_id}", response_model=MediaResponse)
def get_media_detail(media_id: int, session: Session = Depends(get_session)):
    """
    获取单个任务的基础状态
    """
    media = session.get(SourceMedia, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="任务不存在")
    return media


@router.get("/media/{media_id}/transcript", response_model=TranscriptResponse)
def get_media_transcript(media_id: int, session: Session = Depends(get_session)):
    """
    按需加载逐字稿 (对应 TranscriptResponse)
    """
    media = session.get(SourceMedia, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="任务不存在")
    statement = select(TranscriptSegment).where(TranscriptSegment.media_id == media_id).order_by(TranscriptSegment.start_time)
    segments = session.exec(statement).all()
    return {
        "media_id": media_id,
        "count": len(segments),
        "segments": segments,
    }


@router.get("/media/{media_id}/summary", response_model=SummaryResponse)
def get_media_summary(
    media_id: int,
    summary_type: str = "detail",
    session: Session = Depends(get_session),
):
    """
    获取 AI 总结 (默认返回该类型下最新的一条)
    """
    media = session.get(SourceMedia, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="任务不存在")
    statement = (
        select(Summary).where(Summary.media_id == media_id).where(Summary.summary_type == summary_type).order_by(Summary.created_at.desc())  # 最新的在前面
    )
    all_summaries = session.exec(statement).all()
    return {
        "media_id": media_id,
        "summaries": all_summaries,
    }
