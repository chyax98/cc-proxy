"""
Claude 适配器模块

统一使用 common.adapters 作为基类
"""

from common.adapters import AdapterContext, ClientAdapter, DefaultAdapter, TransformResult

from .cherry_studio import CherryStudioAdapter
from .claude_code import ClaudeCodeAdapter
from .manager import AdapterManager, adapter_manager

__all__ = [
    # 从 common 导入
    "AdapterContext",
    "ClientAdapter",
    "DefaultAdapter",
    "TransformResult",
    # 本地实现
    "CherryStudioAdapter",
    "ClaudeCodeAdapter",
    "AdapterManager",
    "adapter_manager",
]
