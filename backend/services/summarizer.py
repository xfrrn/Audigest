import re
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlmodel import Session

from backend.models import Summary
from backend.services.llm_factory import LLMService


class Summarizer:
    def __init__(self):
        self.llm = LLMService()
        self.prompt_dir = Path(__file__).parent.parent / "prompts"

    def _load_prompt(self, prompt_name: str) -> str:
        file_path = self.prompt_dir / f"{prompt_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt 文件未找到: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def summarize_content(self, session: Session, media_id: int, transcript_path: str) -> Optional[Summary]:
        logger.info(f"🧠 [Summarizer] 开始分析 MediaID: {media_id}")
        txt_path = Path(transcript_path)
        if not txt_path.exists():
            txt_path = txt_path.with_suffix(".txt")
            if not txt_path.exists():
                raise FileNotFoundError(f"转录文件未找到: {transcript_path}")
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            logger.warning("⚠️ 转录内容为空，跳过总结")
            return None
        try:
            system_prompt = self._load_prompt("summary_detail")
            logger.info(f"🤖 [Summarizer] 正在调用 LLM ({self.llm.model})...")
            summary_text = self.llm.generate(system_prompt, content)
            if not summary_text:
                logger.warning("⚠️ LLM 未返回总结内容")
                return None

            tags_list = re.findall(r"#([^#\s.,!?:;\"'()\[\]]+)", summary_text)
            final_tags = []
            for t in tags_list:
                t = t.strip()
                if len(t) > 1 and not t.isnumeric():
                    final_tags.append(t)
            final_tags = final_tags[:10]

            summary_record = Summary(
                media_id=media_id,
                content=summary_text,
                summary_type="detail",
                model_used=self.llm.model,
                tags=final_tags,
            )
            session.add(summary_record)
            session.commit()
            session.refresh(summary_record)

            logger.success(f"✅ [Summarizer] 总结完成 (ID: {summary_record.id}) Tags: {final_tags}")
            return summary_record

        except Exception as e:
            logger.exception("❌ [Summarizer] 总结失败")
            raise e
