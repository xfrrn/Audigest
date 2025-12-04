import re
from urllib.parse import urlparse


class URLParser:
    @staticmethod
    def clean_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        if not url.startswith("http") and "http" in url:
            match = re.search(r"(https?://[^\s]+)", url)
            if match:
                url = match.group(1)
        # 1. Bilibili
        # A: 纯 BV 号
        if re.match(r"^BV[a-zA-Z0-9]+$", url):
            return f"https://www.bilibili.com/video/{url}"
        # B: 标准或分享链接
        if "bilibili.com" in url:
            bv_match = re.search(r"(BV[a-zA-Z0-9]+)", url)
            if bv_match:
                return f"https://www.bilibili.com/video/{bv_match.group(1)}"
            # TODO: 如果没找到 BV 号（比如是 b23.tv 短链），暂且去除参数返回
            if "?" in url:
                url = url.split("?")[0]
            return url.rstrip("/")
        # 2. YouTube
        if "youtube.com" in url or "youtu.be" in url:
            video_id = None
            # A: 短链 (youtu.be/ID)
            if "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            # B: Shorts (youtube.com/shorts/ID)
            elif "/shorts/" in url:
                video_id = url.split("/shorts/")[1].split("?")[0]
            # C: 标准长链 (watch?v=ID)
            elif "v=" in url:
                try:
                    query_part = url.split("?")[1]
                    for p in query_part.split("&"):
                        if p.startswith("v="):
                            video_id = p.split("=")[1]
                            break
                except IndexError:
                    pass
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        # 3. X / Twitter
        if "x.com" in url or "twitter.com" in url:
            if "?" in url:
                url = url.split("?")[0]
            return url.replace("twitter.com", "x.com")
        # 4. 小宇宙
        if "xiaoyuzhoufm.com" in url:
            if "?" in url:
                url = url.split("?")[0]
            return url
        return url

    @staticmethod
    def detect_platform(url: str) -> str:
        url = url.strip()
        if re.match(r"^BV[a-zA-Z0-9]+$", url):
            return "bilibili"
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        if "youtube" in domain or "youtu.be" in domain:
            return "youtube"
        if "bilibili" in domain:
            return "bilibili"
        if "xiaoyuzhoufm" in domain:
            return "xiaoyuzhou"
        if "x.com" in domain or "twitter.com" in domain:
            return "twitter"
        if path.endswith((".xml", ".rss")) or "/feed/" in path or "rss" in domain or "feeds" in domain:
            return "podcast"
        if path.endswith((".mp3", ".m4a", ".wav")):
            return "direct_file"
        return "unknown"
