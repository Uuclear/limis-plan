"""应用配置 (pydantic-settings)"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "MatLIMS"
    app_version: str = "1.0.0"
    secret_key: str = Field(min_length=32)
    session_max_age: int = 604800
    csrf_secret: str = Field(min_length=16)
    database_url: str = Field(default="postgresql+asyncpg://lims:lims@localhost:5432/lims_db")
    database_url_sync: str = Field(default="postgresql://lims:lims@localhost:5432/lims_db")
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_url: str = "redis://localhost:6379/1"
    redis_ws_url: str = "redis://localhost:6379/2"
    file_storage_base_dir: str = "/data/lims/files"
    log_level: str = "INFO"
    log_file: str = "/var/log/lims/app.log"
    celery_broker_url: str = "redis://localhost:6379/3"
    celery_result_backend: str = "redis://localhost:6379/4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
