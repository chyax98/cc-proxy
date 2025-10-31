"""
OpenAI Responses API 响应模型
"""
from typing import Any

from pydantic import BaseModel, Field


class OutputItem(BaseModel):
    """响应输出项"""

    type: str = Field(
        ...,
        description="输出类型，例如 'message' 或 'function_call'",
    )

    content: str | dict[str, Any] = Field(
        ...,
        description="输出内容",
    )

    role: str | None = Field(
        default=None,
        description="消息角色 (message 类型时)",
    )


class UsageInfo(BaseModel):
    """使用量信息"""

    prompt_tokens: int = Field(default=0, description="提示词 token 数量")
    completion_tokens: int = Field(default=0, description="完成 token 数量")
    total_tokens: int = Field(default=0, description="总 token 数量")


class ResponsesResponse(BaseModel):
    """
    OpenAI Responses API 响应

    参考: https://platform.openai.com/docs/api-reference/responses
    """

    id: str = Field(
        ...,
        description="唯一响应 ID",
    )

    object: str = Field(
        default="response",
        description="对象类型",
    )

    created_at: int = Field(
        ...,
        description="创建时间戳",
    )

    status: str = Field(
        default="completed",
        description="响应状态 (completed/failed/in_progress)",
    )

    output: list[OutputItem] = Field(
        default_factory=list,
        description="输出项列表",
    )

    usage: UsageInfo = Field(
        default_factory=UsageInfo,
        description="使用量信息",
    )

    model: str | None = Field(
        default=None,
        description="使用的模型",
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="额外的元数据",
    )
