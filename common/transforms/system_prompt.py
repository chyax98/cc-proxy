"""
系统提示词转换器

负责注入 system prompt 或 instructions
"""

from __future__ import annotations

from typing import Any

from .base import TransformContext, Transformer


class SystemPromptTransformer(Transformer):
    """
    系统提示词转换器

    根据目标 API 类型注入系统提示词:
    - Claude API: 注入到 system 字段 (列表格式)
    - OpenAI API: 注入到 instructions 字段 (字符串格式)
    """

    name = "system_prompt"

    def __init__(self, system_prompt: str | list[dict[str, Any]]):
        """
        初始化转换器

        Args:
            system_prompt: 系统提示词
                - 对于 Claude API: list[dict] (如 [{"type": "text", "text": "..."}])
                - 对于 OpenAI API: str (如 "You are Codex...")
        """
        self.system_prompt = system_prompt

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        注入系统提示词

        逻辑 (100% 保留原有行为):
        - Claude API:
          1. 获取现有 system (可能是 str 或 list)
          2. 如果是 str，转换为 [{"type": "text", "text": str}]
          3. 注入 system_prompt: [*system_prompt, *existing_system]

        - OpenAI API:
          1. 直接设置 instructions 字段

        Args:
            data: 请求数据
            context: 转换上下文

        Returns:
            注入系统提示词后的数据
        """
        if context.target_api == "claude":
            # Claude API: system 字段 (列表格式)
            existing_system = data.get("system", [])

            # 字符串转换为列表格式
            if isinstance(existing_system, str):
                existing_system = [{"type": "text", "text": existing_system}]
            elif not isinstance(existing_system, list):
                existing_system = []

            # 注入系统提示词 (放在最前面)
            if isinstance(self.system_prompt, list):
                data["system"] = [*self.system_prompt, *existing_system]
            else:
                data["system"] = [
                    {"type": "text", "text": str(self.system_prompt)},
                    *existing_system,
                ]

        elif context.target_api == "openai":
            # OpenAI API: instructions 字段 (字符串格式)
            if isinstance(self.system_prompt, str):
                data["instructions"] = self.system_prompt
            elif isinstance(self.system_prompt, list):
                # 如果是列表格式，提取文本
                texts = []
                for item in self.system_prompt:
                    if isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                    elif isinstance(item, str):
                        texts.append(item)
                data["instructions"] = "\n".join(texts)
            else:
                data["instructions"] = str(self.system_prompt)

        return data


__all__ = ["SystemPromptTransformer"]
