from loguru import logger
from openai import OpenAI

from backend.core.config import settings


class LLMService:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.client: OpenAI | None = None
        self.model: str = ""
        self.extra_params: dict = {}
        self._load_config()
        logger.info(f"🤖 [LLM] 服务已加载 | 厂商: {self.provider} | 模型: {self.model}")

    def _load_config(self):
        """配置加载路由表"""
        if self.provider == "deepseek":
            self.client = OpenAI(base_url=settings.DEEPSEEK_BASE_URL, api_key=settings.DEEPSEEK_API_KEY)
            self.model = settings.DEEPSEEK_MODEL
        elif self.provider == "ollama":
            self.client = OpenAI(base_url=settings.OLLAMA_BASE_URL, api_key=settings.OLLAMA_API_KEY)
            self.model = settings.OLLAMA_MODEL
            self.extra_params = {"options": {"num_ctx": settings.OLLAMA_CONTEXT}}
        elif self.provider == "openai":
            self.client = OpenAI(base_url=settings.OPENAI_BASE_URL, api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        elif self.provider == "ppio":
            self.client = OpenAI(base_url=settings.PPIO_BASE_URL, api_key=settings.PPIO_API_KEY)
            self.model = settings.PPIO_MODEL
        else:
            raise ValueError(f"❌ 不支持的 LLM 厂商: {self.provider}")

    def generate(self, system_prompt: str, user_content: str) -> str | None:
        """通用生成函数"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
                temperature=0.7,
                extra_body=self.extra_params if self.extra_params else None,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.exception(f"❌ [LLM] 调用失败 (厂商: {self.provider})")
            raise e
