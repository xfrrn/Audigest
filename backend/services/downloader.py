import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import feedparser
import requests
import yt_dlp
from bs4 import BeautifulSoup
from loguru import logger

from backend.core.config import settings


class DownloadError(Exception):
    """下载服务专用异常"""

    pass


class YtDlpLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        logger.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        logger.error(f"[yt-dlp] {msg}")


class MediaDownloader:
    def __init__(self, output_dir: str = "data/audio", proxy_url: Optional[str] = None, foreign_domains: Optional[List[str]] = None):
        """
        初始化下载器
        :param output_dir: 音频保存目录
        :param proxy_url: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy_url = proxy_url or settings.PROXY_URL
        self.foreign_domains = foreign_domains or settings.FOREIGN_DOMAINS
        logger.info(f"[Downloader] 初始化完成 | 目录: {self.output_dir} | 代理: {self.proxy_url or '无'}")

    def download(self, url: str) -> Dict[str, Any]:
        clean_url = self._clean_url(url)
        real_url = self._resolve_real_url(clean_url)
        file_uuid = str(uuid.uuid4())

        ydl_opts = self._build_ydl_opts(file_uuid, real_url)

        logger.info(f"[Downloader] 开始处理任务: {real_url}")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(real_url, download=True)

                final_filename = f"{file_uuid}.mp3"
                abs_path = self.output_dir / final_filename

                if not abs_path.exists():
                    raise DownloadError("文件下载流程结束，但在硬盘上未找到 MP3 文件")
                try:
                    rel_path = abs_path.relative_to(os.getcwd())
                except ValueError:
                    rel_path = abs_path

                logger.success(f"✅ [Downloader] 下载成功: {rel_path}")

                return {
                    "success": True,
                    "uuid": file_uuid,
                    "title": info.get("title", "Unknown Title"),
                    "author": info.get("uploader", info.get("artist", "Unknown Author")),
                    "duration": info.get("duration", 0),
                    "platform": info.get("extractor_key", "Custom"),
                    "original_url": clean_url,
                    "local_path": str(rel_path),
                }

        except Exception as e:
            logger.exception(f"[Downloader] 任务失败: {clean_url}")
            raise DownloadError(f"底层下载失败: {str(e)}") from e

    def _build_ydl_opts(self, file_uuid: str, url: str) -> Dict:
        """
        构建 yt-dlp 的配置字典
        """
        opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{self.output_dir}/{file_uuid}.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "logger": YtDlpLogger(),
            "restrictfilenames": True,
            "cachedir": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
                "Referer": "https://www.bilibili.com/",
            },
        }
        if self.proxy_url and any(domain in url for domain in self.foreign_domains):
            logger.info(f"[网络] 检测到外网域名，启用代理: {self.proxy_url}")
            opts["proxy"] = self.proxy_url

        return opts

    def _clean_url(self, url: str) -> str:
        """清洗 URL 参数"""
        url = url.strip()

        if "bilibili.com" in url:
            return url.split("?")[0]

        if ("youtube.com" in url or "youtu.be" in url) and "&" in url:
            if "watch?v=" in url:
                try:
                    base = url.split("watch?v=")[1]
                    video_id = base.split("&")[0]
                    return f"https://www.youtube.com/watch?v={video_id}"
                except Exception:
                    pass

        if ("x.com" in url or "twitter.com" in url) and "?" in url:
            return url.split("?")[0]

        return url

    def _resolve_real_url(self, url: str) -> str:
        if url.endswith(".xml") or "rss" in url or "feed" in url:
            try:
                logger.debug(f"[解析] 正在解析 RSS Feed: {url}")
                feed = feedparser.parse(url)
                if feed.entries:
                    for link in feed.entries[0].links:
                        if link["type"].startswith("audio"):
                            return link["href"]
            except Exception as e:
                logger.warning(f"RSS 解析异常: {e}")

        if "xiaoyuzhoufm.com" in url:
            try:
                logger.debug(f"[解析] 正在解析小宇宙页面: {url}")
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers)
                soup = BeautifulSoup(resp.text, "html.parser")
                meta = soup.find("meta", property="og:audio")
                if meta:
                    return meta["content"]
            except Exception as e:
                logger.warning(f"小宇宙解析异常: {e}")

        return url
