"""
消息规范化转换器

将不同格式的消息转换为标准格式
主要用于 OpenAI Responses API (要求 type="message", content=array)
"""

from __future__ import annotations

import copy
from typing import Any

from .base import TransformContext, Transformer


class MessageNormalizerTransformer(Transformer):
    """
    消息规范化转换器

    适用于 OpenAI Responses API:
    - 要求消息格式: {"type": "message", "role": "user", "content": [...]}
    - content 必须是数组，不能是字符串
    - developer/system 角色需要转换为 user

    逻辑 100% 保留 service-cx/adapters/cherry_studio.py 的原有实现
    """

    name = "message_normalizer"

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        规范化消息格式

        只对 OpenAI API 执行转换
        """
        if context.target_api != "openai":
            return data

        # 只处理 input 字段
        input_data = data.get("input")
        if input_data is not None:
            data["input"] = self._build_input(input_data)

        return data

    @staticmethod
    def _build_input(input_data: Any) -> list[dict[str, Any]]:
        """
        将 input 转换为 Codex 消息数组

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:129-142)
        """
        messages: list[dict[str, Any]] = []

        if isinstance(input_data, list):
            for item in input_data:
                if isinstance(item, dict):
                    messages.append(MessageNormalizerTransformer._normalize_message(item))
                elif isinstance(item, str):
                    messages.append(MessageNormalizerTransformer._string_message(item))
        elif isinstance(input_data, str):
            messages.append(MessageNormalizerTransformer._string_message(input_data))

        return messages

    @staticmethod
    def _string_message(content: str) -> dict[str, Any]:
        """
        将字符串转换为 Codex 消息

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:144-156)
        """
        return {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": content,
                }
            ],
        }

    @staticmethod
    def _normalize_message(message: dict[str, Any]) -> dict[str, Any]:
        """
        规范化单条消息结构

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:158-204)
        """
        original_role = message.get("role")
        role = MessageNormalizerTransformer._normalize_role(original_role)
        raw_content = message.get("content")

        # developer/system → user，内容使用 input_text 块
        if str(original_role).lower() in {"developer", "system"}:
            dev_content_blocks = MessageNormalizerTransformer._convert_content(raw_content)
            if not dev_content_blocks:
                dev_content_blocks = [{"type": "input_text", "text": ""}]
            return MessageNormalizerTransformer._assemble_message(role, dev_content_blocks, message)

        content_blocks: list[dict[str, Any]] = []
        if isinstance(raw_content, list):
            for block in raw_content:
                if isinstance(block, dict):
                    content_blocks.append(copy.deepcopy(block))
                elif isinstance(block, str):
                    content_blocks.append({"type": "input_text", "text": block})
                else:
                    content_blocks.append({"type": "input_text", "text": str(block)})
        elif isinstance(raw_content, str):
            content_blocks.append({"type": "input_text", "text": raw_content})
        elif raw_content is not None:
            content_blocks.append({"type": "input_text", "text": str(raw_content)})

        if not content_blocks:
            content_blocks.append({"type": "input_text", "text": ""})

        normalized = {
            "type": "message",
            "role": role,
            "content": content_blocks,
        }

        # 保留其他字段 (如 attachments)
        for key, value in message.items():
            if key in {"type", "role", "content"}:
                continue
            normalized[key] = copy.deepcopy(value)

        if original_role is None:
            normalized["type"] = "message"

        return normalized

    @staticmethod
    def _convert_content(raw: Any) -> list[dict[str, Any]]:
        """
        转换内容为标准格式

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:206-221)
        """
        content_blocks: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for block in raw:
                if isinstance(block, dict):
                    content_blocks.append(copy.deepcopy(block))
                elif isinstance(block, str):
                    content_blocks.append({"type": "input_text", "text": block})
                else:
                    content_blocks.append({"type": "input_text", "text": str(block)})
        elif isinstance(raw, str):
            content_blocks.append({"type": "input_text", "text": raw})
        elif raw is not None:
            content_blocks.append({"type": "input_text", "text": str(raw)})
        return content_blocks

    @staticmethod
    def _assemble_message(
        role: str, content_blocks: list[dict[str, Any]], original_msg: dict[str, Any]
    ) -> dict[str, Any]:
        """
        组装消息

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:223-234)
        """
        normalized = {
            "type": "message",
            "role": role,
            "content": content_blocks,
        }
        for key, value in original_msg.items():
            if key in {"type", "role", "content"}:
                continue
            normalized[key] = copy.deepcopy(value)
        return normalized

    @staticmethod
    def _normalize_role(role: Any) -> str:
        """
        转换角色名称 (developer/system → user)

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:236-247)
        """
        if not isinstance(role, str):
            return "user"

        role_lower = role.lower()
        if role_lower in {"developer", "system"}:
            return "user"
        if role_lower in {"assistant", "user", "tool"}:
            return role_lower
        return "user"


__all__ = ["MessageNormalizerTransformer"]
