"""
Claude API 请求模型
定义 CherryStudio 和 Claude Code 的标准请求格式
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ==================== 通用模型 ====================


class CacheControl(BaseModel):
    """
    Prompt Caching 缓存控制

    用于 Anthropic Prompt Caching 功能:
    - ephemeral: 临时缓存 5 分钟,节省 90% token 费用
    """

    type: str = "ephemeral"


class SystemBlock(BaseModel):
    """
    System 提示词块

    用于 system 字段,支持多个文本块和缓存控制
    """

    type: str = "text"
    text: str
    cache_control: CacheControl | None = None


class MessageContent(BaseModel):
    """
    消息内容块

    支持多种类型:
    - text: 纯文本
    - image: 图片 (base64 或 URL)
    - tool_use: 工具调用
    - tool_result: 工具结果
    """

    type: str
    text: str | None = None
    cache_control: CacheControl | None = None

    # 其他类型字段 (image, tool_use, tool_result 等)
    model_config = ConfigDict(extra="allow")


class Message(BaseModel):
    """
    对话消息

    role:
    - user: 用户消息
    - assistant: 助手消息

    content:
    - 字符串: 纯文本消息
    - 列表: 多模态内容 (文本、图片、工具调用等)
    """

    role: str
    content: str | list[MessageContent]


class Metadata(BaseModel):
    """
    请求元数据

    user_id: 用户标识,用于 Prompt Caching 和 session 管理
    """

    user_id: str | None = None

    model_config = ConfigDict(extra="allow")



class ThinkingConfig(BaseModel):
    """
    Extended Thinking 配置

    Claude Extended Thinking 是 Anthropic 官方支持的功能,
    允许模型在回答前进行更深入的思考。

    CherryStudio 和 Claude Code 都支持此功能。

    字段:
    - type: "enabled" 启用思考模式 | "disabled" 禁用
    - budget_tokens: 思考阶段的 token 预算 (可选)

    参考: https://docs.anthropic.com/claude/docs/extended-thinking
    """

    type: str  # "enabled" | "disabled"
    budget_tokens: int | None = None


# ==================== Tool 相关模型 ====================


class ToolInputSchema(BaseModel):
    """
    工具输入参数 Schema

    定义工具的输入参数格式 (JSON Schema)
    """

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = Field(
        default=False, alias="additionalProperties"
    )
    schema_ref: str | None = Field(default=None, alias="$schema")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,  # 同时支持 snake_case 和 camelCase
    )


class Tool(BaseModel):
    """
    工具定义

    Claude API 支持的工具格式:
    - name: 工具名称
    - description: 工具描述
    - input_schema: 输入参数 Schema (JSON Schema 格式)

    参考: https://docs.anthropic.com/claude/docs/tool-use
    """

    name: str
    description: str
    input_schema: ToolInputSchema

    model_config = ConfigDict(extra="allow")


# ==================== 请求基类 ====================


class ClaudeRequestBase(BaseModel):
    """
    Claude API 请求基类

    包含所有客户端通用的请求字段
    """

    model: str
    messages: list[Message]
    max_tokens: int = Field(default=8192, ge=1, le=32000)  # 支持 Claude Code 的 21333
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=0)
    stream: bool = False
    stop_sequences: list[str] | None = None

    # System 提示词 (可以是字符串或结构化块列表)
    system: str | list[SystemBlock] | None = None

    # Extended Thinking (Anthropic 官方功能)
    thinking: ThinkingConfig | None = None

    # Metadata (用于 session 管理和 Prompt Caching)
    metadata: Metadata | None = None

    # Tools (工具定义列表)
    tools: list[Tool] | None = None

    model_config = ConfigDict(extra="allow")






