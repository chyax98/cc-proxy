"""
字段解析转换器

负责解析和规范化各种字段
"""

from __future__ import annotations

from typing import Any

from .base import TransformContext, Transformer


class FieldResolverTransformer(Transformer):
    """
    字段解析转换器

    负责解析和规范化:
    - tool_choice
    - parallel_tool_calls
    - reasoning
    - include
    - stream
    - store

    逻辑 100% 保留 service-cx/adapters/cherry_studio.py 的原实现
    """

    name = "field_resolver"

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        解析和规范化字段

        根据目标 API 类型应用不同的规范化逻辑
        """
        if context.target_api == "openai":
            # OpenAI Responses API 字段规范化

            # tool_choice
            if "tool_choice" in data:
                data["tool_choice"] = self._resolve_tool_choice(data["tool_choice"])

            # parallel_tool_calls
            if "parallel_tool_calls" in data:
                data["parallel_tool_calls"] = self._resolve_parallel_calls(
                    data["parallel_tool_calls"]
                )

            # reasoning
            if "reasoning" in data:
                data["reasoning"] = self._build_reasoning(data.get("reasoning"))

            # include
            if "include" in data:
                data["include"] = self._build_include(data.get("include"))

            # stream (强制为 true)
            data["stream"] = True

            # store
            if "store" in data:
                data["store"] = self._resolve_bool(data.get("store"), default=False)

        return data

    @staticmethod
    def _resolve_tool_choice(tool_choice: Any) -> str:
        """
        工具选择策略，默认为 auto

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:320-325)
        """
        if isinstance(tool_choice, str) and tool_choice:
            return tool_choice
        return "auto"

    @staticmethod
    def _resolve_parallel_calls(value: Any) -> bool:
        """
        解析 parallel_tool_calls

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:327-332)
        """
        if isinstance(value, bool):
            return value
        return False

    @staticmethod
    def _resolve_bool(value: Any, *, default: bool = False) -> bool:
        """
        解析布尔字段

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:334-339)
        """
        if isinstance(value, bool):
            return value
        return default

    @staticmethod
    def _build_reasoning(reasoning: Any) -> dict[str, Any]:
        """
        构造 reasoning 字段

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:289-308)
        """
        effort = "high"
        summary = "auto"

        if isinstance(reasoning, dict):
            effort_candidate = reasoning.get("effort")
            if isinstance(effort_candidate, str) and effort_candidate.lower() in {
                "low",
                "medium",
                "high",
            }:
                effort = effort_candidate.lower()

            summary_candidate = reasoning.get("summary")
            if isinstance(summary_candidate, str) and summary_candidate:
                summary = summary_candidate

        return {"effort": effort, "summary": summary}

    @staticmethod
    def _build_include(include: Any) -> list[str]:
        """
        构造 include 列表，确保包含 reasoning.encrypted_content

        逻辑 100% 保留原实现 (service-cx/adapters/cherry_studio.py:310-318)
        """
        include_values: list[str] = ["reasoning.encrypted_content"]
        if isinstance(include, list):
            for item in include:
                if isinstance(item, str) and item and item not in include_values:
                    include_values.append(item)
        return include_values


__all__ = ["FieldResolverTransformer"]
