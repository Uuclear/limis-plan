"""MatLIMS 核心数据库配置
PostgreSQL 16 + SQLAlchemy 2.0 + asyncpg
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.core.config import settings

# 异步引擎 (用于 FastAPI 路由)
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.database_echo,
)

# 同步引擎 (用于 Alembic 迁移)
sync_engine = create_async_engine(
    settings.database_url_sync,
    poolclass=NullPool,
    echo=settings.database_echo,
)

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明式基类
Base = DeclarativeBase()


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入: 数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """首次启动时自动创建所有表 (仅开发环境)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接池"""
    await engine.dispose()
