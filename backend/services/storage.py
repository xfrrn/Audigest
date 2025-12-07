import json
from pathlib import Path
from typing import Dict, List

from loguru import logger
from sqlmodel import Session, col, delete

from backend.core.utils import format_seconds, seconds_to_srt
from backend.models import SourceMedia, TranscriptSegment


class StorageManager:
    def __init__(self, transcript_dir: str = "data/transcripts"):
        self.transcript_dir = Path(transcript_dir)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, session: Session, media_id: int, segments: List[Dict]) -> str:
        media = session.get(SourceMedia, media_id)
        if not media:
            raise ValueError(f"Media ID {media_id} 不存在")
        if media.local_audio_path:
            file_stem = Path(media.local_audio_path).stem
        else:
            file_stem = str(media_id)
        self._save_to_db(session, media_id, segments)
        txt_path = self._save_to_files(file_stem, segments)

        return txt_path

    def _save_to_db(self, session: Session, media_id: int, segments: List[Dict]):
        """将片段存入 PostgreSQL"""
        logger.info(f"💾 [Storage] 正在写入数据库 (MediaID: {media_id})...")

        statement = delete(TranscriptSegment).where(col(TranscriptSegment.media_id) == media_id)
        session.exec(statement)
        db_segments = []
        for seg in segments:
            db_segments.append(TranscriptSegment(media_id=media_id, start_time=seg["start"], end_time=seg["end"], text=seg["text"], speaker_label=seg["speaker"]))
        session.add_all(db_segments)
        session.commit()
        logger.success(f"✅ [Storage] 数据库写入完成，共 {len(db_segments)} 条")

    def _save_to_files(self, file_stem: str, segments: List[Dict]) -> str:
        """生成 .json (元数据), .txt (LLM用), .srt (字幕)"""
        base_path = self.transcript_dir / file_stem
        logger.info(f"💾 [Storage] 正在生成本地文件: {file_stem}...")

        json_path = base_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        txt_path = base_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for seg in segments:
                time_str = format_seconds(seg["start"])
                line = f"[{time_str}] {seg['speaker']}: {seg['text']}\n"
                f.write(line)
        srt_path = base_path.with_suffix(".srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments):
                start = seconds_to_srt(seg["start"])
                end = seconds_to_srt(seg["end"])
                f.write(f"{i + 1}\n{start} --> {end}\n{seg['text']}\n\n")

        logger.success(f"✅ [Storage] 文件生成完毕: {txt_path}")
        return str(txt_path)
