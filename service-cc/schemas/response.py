"""
Claude API 响应模型

基于 Anthropic 官方 SDK 类型定义
参考: anthropic.types.Message, anthropic.types.Usage
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ==================== Usage (令牌使用统计) ====================


class CacheCreation(BaseModel):
    """
    Prompt Caching 缓存创建统计

    按 TTL (Time-To-Live) 分解的缓存 token 统计
    """

    # 具体字段根据实际API返回定义
    # TODO: 需要根据实际响应补充字段


class ServerToolUsage(BaseModel):
    """
    Server Tool 使用统计

    服务端工具调用次数统计
    """

    # 具体字段根据实际API返回定义
    # TODO: 需要根据实际响应补充字段


class Usage(BaseModel):
    """
    令牌使用统计

    Anthropic API 按 token 计费和限流。
    这个模型包含了完整的 token 统计信息,包括:
    - 基础输入/输出 token
    - Prompt Caching 相关 token
    - 服务层级信息

    参考: https://docs.anthropic.com/claude/docs/billing-and-rate-limits
    """

    # 必填字段
    input_tokens: int = Field(
        ..., description="使用的输入 token 数量"
    )
    output_tokens: int = Field(
        ..., description="使用的输出 token 数量"
    )

    # Prompt Caching 相关 (可选)
    cache_creation_input_tokens: int | None = Field(
        default=None,
        description="用于创建缓存条目的输入 token 数量",
    )
    cache_read_input_tokens: int | None = Field(
        default=None,
        description="从缓存读取的输入 token 数量",
    )
    cache_creation: CacheCreation | None = Field(
        default=None,
        description="按 TTL 分解的缓存 token 统计",
    )

    # Server Tool 相关 (可选)
    server_tool_use: ServerToolUsage | None = Field(
        default=None,
        description="服务端工具请求次数",
    )

    # 服务层级 (可选)
    service_tier: Literal["standard", "priority", "batch"] | None = Field(
        default=None,
        description="请求使用的服务层级",
    )


# ==================== ContentBlock (响应内容块) ====================


class ContentBlock(BaseModel):
    """
    响应内容块

    Claude API 响应的 content 是一个数组,每个元素都是一个内容块。
    内容块类型包括:
    - text: 纯文本内容
    - tool_use: 工具调用
    - thinking: 思考过程 (Extended Thinking)

    参考: https://docs.anthropic.com/claude/docs/messages-api
    """

    type: str = Field(..., description="内容块类型: text, tool_use, thinking 等")

    # text 类型字段
    text: str | None = Field(
        default=None,
        description="文本内容 (type=text 时必填)",
    )

    # tool_use 类型字段
    id: str | None = Field(
        default=None,
        description="工具调用 ID (type=tool_use 时必填)",
    )
    name: str | None = Field(
        default=None,
        description="工具名称 (type=tool_use 时必填)",
    )
    input: dict[str, Any] | None = Field(
        default=None,
        description="工具输入参数 (type=tool_use 时必填)",
    )


# ==================== ClaudeResponse (完整响应) ====================


class ClaudeResponse(BaseModel):
    """
    Claude API 响应模型

    基于 Anthropic 官方 SDK: anthropic.types.Message

    这是非流式请求的完整响应格式。
    流式请求的响应格式见 StreamEvent 系列模型。

    参考: https://docs.anthropic.com/claude/reference/messages_post
    """

    id: str = Field(
        ...,
        description="唯一对象标识符 (格式和长度可能随时间变化)",
    )

    type: Literal["message"] = Field(
        default="message",
        description="对象类型 (对于 Message 总是 'message')",
    )

    role: Literal["assistant"] = Field(
        default="assistant",
        description="生成消息的对话角色 (总是 'assistant')",
    )

    content: list[ContentBlock] = Field(
        ...,
        description="模型生成的内容块数组",
    )

    model: str = Field(
        ...,
        description="使用的模型名称",
    )

    stop_reason: (
        Literal[
            "end_turn",
            "max_tokens",
            "stop_sequence",
            "tool_use",
            "pause_turn",
            "refusal",
        ]
        | None
    ) = Field(
        default=None,
        description="停止原因: end_turn, max_tokens, stop_sequence, tool_use, pause_turn, refusal",
    )

    stop_sequence: str | None = Field(
        default=None,
        description="触发的自定义停止序列 (如果有)",
    )

    usage: Usage = Field(
        ...,
        description="计费和限流使用统计",
    )


class StreamEvent(BaseModel):
    """SSE 事件基类"""

    type: str


class MessageStartEvent(StreamEvent):
    """消息开始事件"""

    type: str = "message_start"
    message: dict[str, Any]


class ContentBlockStartEvent(StreamEvent):
    """内容块开始事件"""

    type: str = "content_block_start"
    index: int
    content_block: dict[str, Any]


class ContentBlockDeltaEvent(StreamEvent):
    """内容块增量事件"""

    type: str = "content_block_delta"
    index: int
    delta: dict[str, Any]


class ContentBlockStopEvent(StreamEvent):
    """内容块结束事件"""

    type: str = "content_block_stop"
    index: int


class MessageDeltaEvent(StreamEvent):
    """消息增量事件"""

    type: str = "message_delta"
    delta: dict[str, Any]
    usage: dict[str, int] | None = None


class MessageStopEvent(StreamEvent):
    """消息结束事件"""

    type: str = "message_stop"


class PingEvent(StreamEvent):
    """Ping 事件"""

    type: str = "ping"


class ErrorEvent(StreamEvent):
    """错误事件"""

    type: str = "error"
    error: dict[str, Any]
