from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel


def utc_now():
    return datetime.now(timezone.utc)


# 1. 基础组件
class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utc_now, nullable=False, description="创建时间")
    updated_at: datetime = Field(default_factory=utc_now, nullable=False, sa_column_kwargs={"onupdate": utc_now}, description="最后更新时间")


#  2. 核心媒体表
class SourceMedia(TimestampMixin, table=True):
    __tablename__ = "source_media"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)

    original_url: str = Field(unique=True, index=True, description="清洗后的原始链接")
    title: str = Field(index=True, description="视频/播客标题")
    author: Optional[str] = Field(default=None, description="频道名或作者")
    platform: str = Field(default="unknown", index=True, description="来源平台: youtube/bilibili/rss/...")
    duration: Optional[int] = Field(default=None, description="时长(秒)")
    status: str = Field(default="pending", index=True)
    local_audio_path: Optional[str] = Field(default=None, description="本地音频文件的相对路径")
    error_msg: Optional[str] = Field(default=None, description="最近一次报错信息")
    segments: List["TranscriptSegment"] = Relationship(back_populates="media", sa_relationship_kwargs={"cascade": "all, delete"})
    summaries: List["Summary"] = Relationship(back_populates="media", sa_relationship_kwargs={"cascade": "all, delete"})
    export_logs: List["ExportLog"] = Relationship(back_populates="media", sa_relationship_kwargs={"cascade": "all, delete"})


# 3. 逐字稿切片表
class TranscriptSegment(SQLModel, table=True):
    __tablename__ = "transcript_segment"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="source_media.id", index=True)
    start_time: float = Field(description="开始时间(秒)")
    end_time: float = Field(description="结束时间(秒)")
    text: str = Field(sa_column=Column(Text), description="文本内容")
    speaker_label: str = Field(description="原始标签, 如 SPEAKER_01")
    speaker_name: Optional[str] = Field(default=None, description="真实人名, 如 Elon Musk")
    media: SourceMedia = Relationship(back_populates="segments")


# 4. 智能总结表
class Summary(TimestampMixin, table=True):
    __tablename__ = "summary"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="source_media.id", index=True)
    summary_type: str = Field(default="detail", description="类型: detail/short/mindmap")
    content: str = Field(sa_column=Column(Text), description="Markdown 格式的总结内容")
    tags: List[str] = Field(default=[], sa_column=Column(JSONB))
    model_used: str = Field(default="gpt-4o", description="使用的 LLM 模型")
    media: SourceMedia = Relationship(back_populates="summaries")


# 5. 导出记录表
class ExportLog(TimestampMixin, table=True):
    __tablename__ = "export_log"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="source_media.id", index=True)
    target_platform: str = Field(description="目标平台: notion/obsidian/feishu")
    external_id: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="success")
    error_msg: Optional[str] = Field(default=None)
    media: SourceMedia = Relationship(back_populates="export_logs")
