"""
Claude Service 主应用
处理 Claude API 请求转换和代理
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import settings
from common.http_client import http_client
from common.logger import configure_logging, get_logger

from .router import router as claude_router

# 配置日志系统
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(
        "claude_service_starting",
        app_name="Claude Service",
        version=settings.app_version,
        anthropic_base_url=settings.anthropic_base_url,
    )

    yield

    # 关闭时的清理逻辑
    logger.info("claude_service_shutdown")
    await http_client.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="Claude Service",
    version=settings.app_version,
    description="Claude API 请求转换和代理服务",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """根路径 - 服务信息"""
    return {
        "service": "Claude Service",
        "version": settings.app_version,
        "description": "Claude API 请求转换和代理服务",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "claude-service",
        "version": settings.app_version,
    }


# 注册路由
app.include_router(claude_router, tags=["claude"])


if __name__ == "__main__":
    import uvicorn

    # 开发环境运行服务器
    # 生产环境请使用: python start.py (会自动使用 gunicorn)
    uvicorn.run(
        "service-cc.main:app",
        host=settings.claude_service_host,
        port=settings.claude_service_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        access_log=True,
    )
