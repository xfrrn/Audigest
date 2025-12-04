from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 代理地址
    PROXY_URL: Optional[str] = "http://127.0.0.1:7890"

    # 👇 把这个列表搬到这里，作为默认值
    FOREIGN_DOMAINS: List[str] = ["youtube", "twitter", "x", "tiktok", "RSS"]

    class Config:
        env_file = ".env"


# 实例化配置
settings = Settings()
