from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from backend.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    logger.info("🔄 正在初始化数据库表结构...")
    SQLModel.metadata.create_all(engine)
    logger.info("✅ 数据库表结构创建完成！")
