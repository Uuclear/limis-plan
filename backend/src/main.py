"""FastAPI 应用工厂"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_csrf import CSRFMiddleware

from src.core.config import settings
from src.core.db import init_db, close_db
from src.api.routes import (
    auth, samples, orders, files, reports,
    records, workflows, equipment, standards,
    billing, quality, system
)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_max_age,
        same_site="lax",
    )
    app.add_middleware(
        CSRFMiddleware,
        secret=settings.csrf_secret,
    )

    @app.on_event("startup")
    async def startup():
        await init_db()

    @app.on_event("shutdown")
    async def shutdown():
        await close_db()

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(samples.router, prefix="/api/v1/samples", tags=["样品"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["委托"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["文件"])
    app.include_router(records.router, prefix="/api/v1/records", tags=["原始记录"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["工作流"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["报告"])
    app.include_router(equipment.router, prefix="/api/v1/equipment", tags=["设备"])
    app.include_router(standards.router, prefix="/api/v1/standards", tags=["标准方法"])
    app.include_router(billing.router, prefix="/api/v1/billing", tags=["计费"])
    app.include_router(quality.router, prefix="/api/v1/quality", tags=["质量管控"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["系统配置"])
    return app
