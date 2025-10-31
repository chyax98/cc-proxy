"""
统一适配器模块

提供 service-cc (Claude) 和 service-cx (Codex) 共用的适配器基类
"""
from .base import AdapterContext, ClientAdapter, DefaultAdapter, TransformResult

__all__ = [
    # 数据类
    "AdapterContext",
    "TransformResult",
    # 适配器
    "ClientAdapter",
    "DefaultAdapter",
]
