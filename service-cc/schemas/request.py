"""
Claude 请求模型

包含所有客户端的请求格式定义
"""

from pydantic import ConfigDict, Field

from .base import ClaudeRequestBase, Metadata, SystemBlock, Tool


class CherryStudioRequest(ClaudeRequestBase):
    """
    CherryStudio 客户端请求模型

    继承自 ClaudeRequestBase,添加 CherryStudio 特有的字段约束

    特点:
    - 包含 thinking 字段 (CherryStudio 支持的扩展功能)
    - system 可以是字符串或结构化块列表
    - 可能不包含 tools 定义 (需要由服务端注入)
    - 不包含 cache_control (需要由服务端注入)
    - 支持流式响应 (stream=true)

    与 Claude Code 的区别:
    - system 可以是简单字符串
    - tools 可选 (需要服务端注入)
    - metadata 可选 (需要服务端注入)
    - max_tokens 默认 5120 (更小)

    示例:
    ```python
    request = CherryStudioRequest(
        model="claude-sonnet-4-5-20250929",
        system=[
            SystemBlock(type="text", text="Tool use instructions...")
        ],
        messages=[
            Message(
                role="user",
                content=[
                    MessageContent(type="text", text="Hello")
                ]
            )
        ],
        thinking=ThinkingConfig(type="enabled", budget_tokens=1024),
        max_tokens=5120,
        stream=True
    )
    ```
    """

    # 重写默认值 (CherryStudio 特有的配置)
    max_tokens: int = Field(default=5120, ge=1, le=8192)

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "model": "claude-sonnet-4-5-20250929",
                "system": [
                    {
                        "type": "text",
                        "text": "In this environment you have access to a set of tools...",
                    }
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "1"}],
                    }
                ],
                "thinking": {"type": "enabled", "budget_tokens": 1024},
                "max_tokens": 5120,
                "stream": True,
            }
        },
    )


class ClaudeCodeRequest(ClaudeRequestBase):
    """
    Claude Code 标准请求模型

    继承自 ClaudeRequestBase,添加 Claude Code 特有的字段约束

    特点:
    - system 必须为结构化块列表 (含 cache_control)
    - messages 包含用户配置和项目文档 (以 <system-reminder> 形式)
    - tools 必须包含完整的 MCP 工具定义
    - metadata 必须包含 session 管理的 user_id
    - 启用 Prompt Caching (通过 cache_control)
    - 支持 thinking 字段 (Extended Thinking)

    示例:
    ```python
    request = ClaudeCodeRequest(
        model="claude-sonnet-4-5-20250929",
        system=[
            SystemBlock(
                type="text",
                text="You are Claude Code...",
                cache_control=CacheControl(type="ephemeral")
            )
        ],
        messages=[
            Message(
                role="user",
                content=[
                    MessageContent(type="text", text="Hello"),
                    MessageContent(
                        type="text",
                        text="<system-reminder>...</system-reminder>",
                        cache_control=CacheControl(type="ephemeral")
                    )
                ]
            )
        ],
        tools=[...],  # MCP 工具定义
        metadata=Metadata(user_id="user_xxx_session_xxx"),
        max_tokens=21333
    )
    ```
    """

    # Claude Code 特有的必填字段
    system: list[SystemBlock]  # 必须为结构化块列表
    metadata: Metadata  # 必须包含 user_id
    tools: list[Tool]  # 必须包含工具定义

    # 重写默认值 (Claude Code 特有的配置)
    max_tokens: int = Field(default=21333, ge=1, le=32000)
    temperature: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "model": "claude-sonnet-4-5-20250929",
                "system": [
                    {
                        "type": "text",
                        "text": "You are Claude Code...",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Hello"},
                            {
                                "type": "text",
                                "text": "<system-reminder>Context info</system-reminder>",
                                "cache_control": {"type": "ephemeral"},
                            },
                        ],
                    }
                ],
                "tools": [
                    {
                        "name": "Bash",
                        "description": "Execute bash commands",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string"}
                            },
                            "required": ["command"],
                        },
                    }
                ],
                "metadata": {"user_id": "user_xxx_session_xxx"},
                "max_tokens": 21333,
                "temperature": 1.0,
            }
        },
    )
