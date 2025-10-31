"""
结构化日志系统
使用 structlog 提供 JSON 格式的结构化日志
"""
import logging
import sys

import structlog
from structlog.types import EventDict, WrappedLogger

from .config import settings


def add_app_context(logger: WrappedLogger, name: str, event_dict: EventDict) -> EventDict:
    """添加应用上下文"""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    return event_dict


def configure_logging() -> None:
    """配置日志系统"""
    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # 配置 structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # 根据格式选择渲染器
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取 logger 实例"""
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def should_log_body() -> bool:
    """
    判断是否应该记录请求/响应体

    Returns:
        bool: True 表示记录详细日志 (测试环境), False 表示不记录 (生产环境)
    """
    return settings.is_test_environment


# 初始化日志系统
configure_logging()
