from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class MediaCreateRequest(BaseModel):
    url: HttpUrl


class TranscriptItem(BaseModel):
    start_time: float
    end_time: float
    text: str
    speaker_label: str


class SummaryItem(BaseModel):
    summary_type: str
    content: str
    tags: List[str] = []
    model_used: str
    updated_at: datetime


class MediaResponse(BaseModel):
    id: int
    original_url: str
    title: Optional[str] = "获取中..."
    author: Optional[str] = None
    platform: str
    duration: Optional[int] = None
    status: str
    error_msg: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptResponse(BaseModel):
    media_id: int
    count: int
    segments: List[TranscriptItem]


class SummaryResponse(BaseModel):
    media_id: int
    summaries: List[SummaryItem]
