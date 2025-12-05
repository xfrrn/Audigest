from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROXY_URL: Optional[str] = "http://127.0.0.1:7890"
    FOREIGN_DOMAINS: List[str] = ["youtube", "twitter", "x", "tiktok", "RSS"]
    HF_TOKEN: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # LLM 相关配置
    DEFAULT_LLM_PROVIDER: str = "deepseek"

    # 厂商 1: DeepSeek
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 厂商 2: Ollama (本地)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = "ollama"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_CONTEXT: int = 16000

    # 厂商 3: OpenAI (官方)
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    # 厂商 4: PPIO
    PPIO_BASE_URL: str = "https://api.ppinfra.com/openai"
    PPIO_API_KEY: Optional[str] = None
    PPIO_MODEL: str = "deepseek/deepseek-v3.2"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
