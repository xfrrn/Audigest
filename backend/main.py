from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.routes import router as api_router
from backend.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理器：
    - 启动前：初始化数据库
    - 运行中：提供服务
    - 关闭后：清理资源 (比如关闭 Redis 连接池，如果以后需要的话)
    """
    logger.info("🚀 Audigest API 正在启动...")

    # 1. 自动建表 (防止第一次运行报错)
    init_db()
    yield
    logger.info("👋 Audigest API 已关闭")


app = FastAPI(
    title="Audigest API",
    description="Video/Podcast Summarizer Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """健康检查接口"""
    return {"message": "Welcome to Audigest API", "docs_url": "/docs", "redoc_url": "/redoc"}
