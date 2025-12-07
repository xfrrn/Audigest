import re

from loguru import logger


def detect_language_from_title(title: str) -> str:
    if not title:
        return "auto"
    if re.search(r"[\u4e00-\u9fff]", title):
        logger.debug(f"🇨🇳 [Utils] 检测到中文标题: '{title}' -> 策略: zh")
        return "zh"
    logger.debug(f"🌐 [Utils] 标题无中文: '{title}' -> 策略: auto")
    return "auto"


def format_seconds(seconds: float) -> str:
    """
    将秒数转换为 MM:SS 格式
    例如: 75.5 -> '01:15'
    用于: 生成给 LLM 看的 .txt 文件
    """
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def seconds_to_srt(seconds: float) -> str:
    """
    将秒数转换为 SRT 字幕时间戳格式
    格式: HH:MM:SS,ms
    例如: 75.5 -> '00:01:15,500'
    用于: 生成 .srt 字幕文件
    """
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"
