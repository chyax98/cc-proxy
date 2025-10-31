#!/usr/bin/env python3
"""
CC-Proxy 统一启动脚本 (优化版)
根据环境变量自动选择 uvicorn (开发) 或 gunicorn (生产)
支持资源限制和性能优化
"""
import gc
import importlib.util
import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from common.config import settings  # noqa: E402
from common.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def optimize_memory():
    """优化内存使用"""
    # 强制垃圾回收
    gc.collect()

    # 设置垃圾回收阈值 (减少内存占用)
    gc.set_threshold(700, 10, 10)

    # 在容器环境中设置更激进的内存优化
    if os.getenv("CONTAINER_MODE") == "true":
        # 更频繁的垃圾回收
        gc.set_threshold(500, 5, 5)

    logger.info("memory_optimized", container_mode=os.getenv("CONTAINER_MODE") == "true")


def start_development():
    """开发环境启动 (uvicorn + reload + 内存优化)"""
    import uvicorn

    # 内存优化
    optimize_memory()

    logger.info(
        "starting_development_server",
        service="development",
        claude_port=settings.claude_service_port,
        codex_port=settings.codex_service_port,
        environment=settings.environment,
        log_level=settings.log_level,
        detailed_logging=settings.is_test_environment,
        container_mode=os.getenv("CONTAINER_MODE") == "true",
    )

    # 启动 service-cc (Claude)
    if os.fork() == 0:
        optimize_memory()  # 子进程也需要优化
        uvicorn.run(
            "service-cc.main:app",
            host=settings.claude_service_host,
            port=settings.claude_service_port,
            reload=True,
            log_level=settings.log_level.lower(),
            # 内存优化配置
            access_log=False,  # 减少日志开销
            use_colors=False,  # 在容器中关闭颜色
        )
        sys.exit(0)

    # 启动 service-cx (Codex)
    optimize_memory()  # 主进程也需要优化
    uvicorn.run(
        "service-cx.main:app",
        host=settings.codex_service_host,
        port=settings.codex_service_port,
        reload=True,
        log_level=settings.log_level.lower(),
        # 内存优化配置
        access_log=False,
        use_colors=False,
    )


def start_production():
    """生产环境启动 (gunicorn + 内存优化 + 资源限制)"""
    import subprocess

    # 内存优化
    optimize_memory()

    # 根据 CONTAINER_MODE 和可用内存调整 worker 数量
    import psutil
    available_memory_gb = psutil.virtual_memory().available / (1024**3)

    # 容器环境或低内存环境使用更少的 workers
    if os.getenv("CONTAINER_MODE") == "true" or available_memory_gb < 2:
        worker_count = 2
        max_requests = 100  # 更频繁的 worker 重启
        max_requests_jitter = 20
    else:
        worker_count = min(4, max(2, int(available_memory_gb / 0.5)))  # 每 512MB 一个 worker
        max_requests = 1000
        max_requests_jitter = 100

    logger.info(
        "starting_production_server",
        service="production",
        claude_port=settings.claude_service_port,
        codex_port=settings.codex_service_port,
        environment=settings.environment,
        worker_count=worker_count,
        available_memory_gb=round(available_memory_gb, 2),
        max_requests=max_requests,
        max_requests_jitter=max_requests_jitter,
        container_mode=os.getenv("CONTAINER_MODE") == "true",
    )

    # gunicorn 基础配置
    base_gunicorn_config = [
        "gunicorn",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--worker-connections", "1000",  # 减少连接数
        "--max-requests", str(max_requests),  # worker 处理请求数后重启
        "--max-requests-jitter", str(max_requests_jitter),
        "--preload",  # 预加载应用，节省内存
        "--timeout", "30",  # 减少超时时间
        "--keep-alive", "2",  # 减少保持连接时间
        "--log-level", settings.log_level.lower(),
        "--access-logfile", "-",
        "--error-logfile", "-",
    ]

    # 启动 service-cc (Claude)
    claude_cmd = base_gunicorn_config + [
        "service-cc.main:app",
        "--bind", f"{settings.claude_service_host}:{settings.claude_service_port}",
        "--workers", str(worker_count),
        "--name", "claude-worker",
    ]

    # 启动 service-cx (Codex)
    codex_cmd = base_gunicorn_config + [
        "service-cx.main:app",
        "--bind", f"{settings.codex_service_host}:{settings.codex_service_port}",
        "--workers", str(worker_count),
        "--name", "codex-worker",
    ]

    logger.debug(
        "gunicorn_commands",
        claude_command=" ".join(claude_cmd),
        codex_command=" ".join(codex_cmd),
    )

    # 启动两个服务
    try:
        claude_process = subprocess.Popen(claude_cmd)
        codex_process = subprocess.Popen(codex_cmd)

        # 等待进程
        claude_process.wait()
        codex_process.wait()
    except KeyboardInterrupt:
        logger.info("services_stopped_by_user")
        if 'claude_process' in locals():
            claude_process.terminate()
            claude_process.wait()
        if 'codex_process' in locals():
            codex_process.terminate()
            codex_process.wait()
    except Exception as e:
        logger.error("production_startup_failed", error=str(e), error_type=type(e).__name__)
        if os.getenv("DEBUG", "false").lower() == "true":
            logger.error("production_startup_traceback", traceback=traceback.format_exc())
        sys.exit(1)


def main():
    """主函数 - 根据环境选择启动方式"""
    try:
        # 检查是否安装了必要的依赖
        if importlib.util.find_spec("uvicorn") is None:
            logger.error("uvicorn_not_installed")
            logger.error("fix_run_uv_sync")
            sys.exit(1)

        # 根据环境选择启动方式
        if settings.environment.lower() in ("production", "prod"):
            # 生产环境检查 gunicorn
            if importlib.util.find_spec("gunicorn") is None:
                logger.error("gunicorn_not_installed")
                logger.error("fix_run_uv_add_gunicorn")
                sys.exit(1)

            start_production()
        else:
            # 开发/测试环境使用 uvicorn
            start_development()

    except KeyboardInterrupt:
        logger.info("startup_interrupted_by_user")
        sys.exit(0)
    except Exception as e:
        logger.error("startup_failed", error=str(e), error_type=type(e).__name__)
        if os.getenv("DEBUG", "false").lower() == "true":
            logger.error("startup_traceback", traceback=traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
