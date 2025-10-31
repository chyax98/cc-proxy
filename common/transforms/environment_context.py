"""
环境上下文转换器

负责添加当前工作目录等环境信息
"""

from __future__ import annotations

import os
from typing import Any

from .base import TransformContext, Transformer


class EnvironmentContextTransformer(Transformer):
    """
    环境上下文转换器

    为 Codex 添加环境上下文消息 (当前工作目录)

    逻辑 100% 保留 service-cx/formats/environment_context.py 的原实现
    """

    name = "environment_context"

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        添加环境上下文消息

        只对 OpenAI API 执行转换
        """
        if context.target_api != "openai":
            return data

        input_messages = data.get("input", [])

        # 如果已经存在环境上下文，则跳过
        if not self._has_environment_context(input_messages):
            env_message = self._build_environment_context_message()
            input_messages.insert(0, env_message)
            data["input"] = input_messages

        return data

    @staticmethod
    def _has_environment_context(messages: list[dict[str, Any]]) -> bool:
        """
        检查是否已经存在环境上下文

        逻辑 100% 保留原实现 (service-cx/formats/environment_context.py:16-30)
        """
        if not messages:
            return False

        first_message = messages[0]
        if not isinstance(first_message, dict):
            return False

        if first_message.get("role") != "user":
            return False

        content = first_message.get("content", [])
        if not content or not isinstance(content, list):
            return False

        first_content = content[0]
        if not isinstance(first_content, dict):
            return False

        text = first_content.get("text", "")
        return "Current directory:" in text

    @staticmethod
    def _build_environment_context_message() -> dict[str, Any]:
        """
        生成环境上下文消息

        逻辑 100% 保留原实现 (service-cx/formats/environment_context.py:33-44)
        """
        cwd = os.getcwd()
        return {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Current directory: {cwd}",
                }
            ],
        }


__all__ = ["EnvironmentContextTransformer"]
