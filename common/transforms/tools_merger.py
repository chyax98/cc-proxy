"""
工具合并转换器

负责合并默认工具和客户端工具
"""

from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import Any

from common.logger import get_logger

from .base import TransformContext, Transformer

logger = get_logger(__name__)


class ToolsMergerTransformer(Transformer):
    """
    工具合并转换器

    策略:
    1. 始终以默认工具开始
    2. 客户端工具直接 append (不过滤、不去重)

    逻辑 100% 保留 service-cx/adapters/cherry_studio.py:249-287
    """

    name = "tools_merger"

    def __init__(self, default_tools: list[dict[str, Any]]):
        """
        初始化转换器

        Args:
            default_tools: 默认工具列表
        """
        self.default_tools = default_tools

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        合并工具定义

        逻辑 100% 保留原实现
        """
        # 从默认工具开始
        merged = copy.deepcopy(self.default_tools)

        # 检查客户端是否提供了工具
        client_tools = data.get("tools")
        if isinstance(client_tools, Iterable) and not isinstance(client_tools, (str, bytes)):
            client_tool_list = [t for t in client_tools if isinstance(t, dict)]

            # 直接 append 客户端工具
            if client_tool_list:
                merged.extend(copy.deepcopy(client_tool_list))
                logger.info(
                    "appended_client_tools",
                    default_count=len(self.default_tools),
                    client_count=len(client_tool_list),
                    total_count=len(merged),
                )
            else:
                logger.debug(
                    "using_default_tools_only",
                    tool_count=len(self.default_tools),
                    reason="no tools from client",
                )
        else:
            logger.debug(
                "using_default_tools_only",
                tool_count=len(self.default_tools),
                reason="client did not provide tools",
            )

        data["tools"] = merged
        return data


__all__ = ["ToolsMergerTransformer"]
