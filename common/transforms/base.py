"""
转换器基类和上下文定义
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransformContext:
    """
    转换上下文

    提供转换过程中需要的额外信息
    """

    target_api: str  # 目标 API: "claude" 或 "openai"
    client_type: str  # 客户端类型: "cherry_studio", "claude_code", 等
    raw_headers: dict[str, str] = field(default_factory=dict)  # 原始请求头
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据


class Transformer(ABC):
    """
    转换器基类

    每个转换器负责一种特定的转换操作
    转换器应该是无状态的，可以被多次调用
    """

    name: str = "base"

    @abstractmethod
    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        执行转换操作

        Args:
            data: 待转换的数据（会被修改）
            context: 转换上下文

        Returns:
            转换后的数据
        """
        pass

    def validate(self, data: dict[str, Any]) -> bool:
        """
        验证转换结果 (可选)

        Args:
            data: 转换后的数据

        Returns:
            是否验证通过
        """
        return True


__all__ = ["Transformer", "TransformContext"]
