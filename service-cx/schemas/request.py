"""
OpenAI Responses API 请求模型
"""
from typing import Any

from pydantic import BaseModel, Field


class ResponsesRequest(BaseModel):
    """
    OpenAI Responses API 请求

    参考: https://platform.openai.com/docs/api-reference/responses
    """

    model: str = Field(
        ...,
        description="要使用的模型 ID，例如 'gpt-4o' 或 'gpt-4o-mini'",
    )

    input: str | list[dict[str, Any]] = Field(
        ...,
        description="输入内容，可以是字符串或消息数组",
    )

    tools: list[dict[str, Any]] | None = Field(
        default=None,
        description="工具定义列表，用于函数调用",
    )

    store: bool = Field(
        default=False,
        description="是否存储此响应",
    )

    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="采样温度，范围 0.0-2.0",
    )

    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        description="最大输出 token 数量",
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="额外的元数据",
    )

    # 客户端特有字段
    reasoning: dict[str, Any] | None = Field(
        default=None,
        description="推理配置，支持 effort (low/medium/high) 和 summary (auto)",
    )

    stream: bool = Field(
        default=False,
        description="是否使用流式响应",
    )

    tool_choice: str | None = Field(
        default=None,
        description="工具选择策略 (auto, none, required)",
    )

    parallel_tool_calls: bool = Field(
        default=False,
        description="是否允许并行工具调用",
    )

    include: list[str] | None = Field(
        default=None,
        description="包含的额外字段，如 reasoning.encrypted_content",
    )

    prompt_cache_key: str | None = Field(
        default=None,
        description="提示缓存键，用于优化缓存命中率",
    )

    instructions: str | None = Field(
        default=None,
        description="系统指令 (类似 Anthropic 的 system)",
    )
