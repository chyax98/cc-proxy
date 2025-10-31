"""
统一适配器基类

用于 service-cc (Claude) 和 service-cx (Codex) 的客户端请求转换
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterContext:
    """
    适配器上下文 (传递请求元信息)

    包含原始请求的所有信息,供适配器进行检测和转换
    """

    raw_body: dict[str, Any]
    """原始请求体"""

    raw_headers: dict[str, str]
    """原始请求头 (小写 key)"""

    client_ip: str | None = None
    """客户端 IP 地址 (可选)"""

    request_id: str | None = None
    """请求 ID (可选,用于日志追踪)"""


@dataclass
class TransformResult:
    """
    转换结果 (包含转换后的 body + headers + metadata)

    适配器转换后返回的结果,包含:
    - 转换后的请求体 (传递给 API SDK)
    - 需要注入的额外 headers
    - 元数据 (用于日志记录)
    """

    body: dict[str, Any]
    """转换后的请求体"""

    extra_headers: dict[str, str] = field(default_factory=dict)
    """需要注入的额外 headers (如 anthropic-beta, openai-beta 等)"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """元数据 (用于日志记录,如 adapter 名称、客户端版本等)"""


class ClientAdapter(ABC):
    """
    客户端适配器基类 (统一接口)

    每个适配器负责:
    1. 检测客户端类型 (detect)
    2. 转换请求格式 (transform)
    3. 提供适配器元信息 (name, priority, version)

    优先级说明:
    - 数字越大优先级越高
    - 官方客户端优先级最高 (如 Codex CLI: 100, Claude Desktop: 100)
    - 第三方客户端中等优先级 (如 CherryStudio: 50)
    - 默认适配器优先级最低 (-999,兜底)
    """

    # 适配器元信息
    name: str = "base"
    """适配器名称"""

    priority: int = 0
    """优先级 (数字越大优先级越高)"""

    version: str = "1.0.0"
    """适配器版本"""

    @abstractmethod
    def detect(self, ctx: AdapterContext) -> bool:
        """
        检测是否匹配此适配器

        Args:
            ctx: 适配器上下文 (包含原始请求信息)

        Returns:
            bool: 是否匹配此适配器

        示例:
            def detect(self, ctx: AdapterContext) -> bool:
                user_agent = ctx.raw_headers.get("user-agent", "").lower()
                return "cherrystudio" in user_agent
        """

    @abstractmethod
    def transform(self, ctx: AdapterContext) -> TransformResult:
        """
        转换请求格式

        Args:
            ctx: 适配器上下文 (包含原始请求信息)

        Returns:
            TransformResult: 转换结果 (包含 body + extra_headers + metadata)

        示例:
            def transform(self, ctx: AdapterContext) -> TransformResult:
                body = ctx.raw_body.copy()

                # 注入 system prompt / instructions
                body["system"] = CLAUDE_CODE_SYSTEM  # Claude
                # 或
                body["instructions"] = CODEX_INSTRUCTIONS  # Codex

                # 移除不兼容字段
                body.pop("thinking", None)  # Claude

                return TransformResult(
                    body=body,
                    extra_headers={
                        "anthropic-beta": "...",  # Claude
                        # 或
                        "openai-beta": "responses=experimental",  # Codex
                    },
                    metadata={"adapter": self.name},
                )
        """

    def validate(self, result: TransformResult) -> None:
        """
        可选: 验证转换结果

        Args:
            result: 转换结果

        Raises:
            ValueError: 转换结果无效

        示例:
            def validate(self, result: TransformResult) -> None:
                if "model" not in result.body:
                    raise ValueError("Missing required field: model")
        """


class DefaultAdapter(ClientAdapter):
    """
    默认适配器 (兜底)

    优先级最低,不做任何转换,直接透传
    假设请求体已经是标准 API 格式
    """

    name = "default"
    priority = -999  # 最低优先级
    version = "1.0.0"

    def detect(self, ctx: AdapterContext) -> bool:
        """默认适配器始终匹配 (兜底)"""
        return True

    def transform(self, ctx: AdapterContext) -> TransformResult:
        """
        直接透传,最小化转换

        注意: 只修复必需字段,由各服务的 proxy 层负责其他逻辑
        """
        import copy

        body = copy.deepcopy(ctx.raw_body)

        # 修复 stream 字段 (88code 要求必须为布尔值,不能为 null)
        if "stream" not in body or body["stream"] is None:
            body["stream"] = False
        elif not isinstance(body["stream"], bool):
            body["stream"] = bool(body["stream"])

        return TransformResult(
            body=body,
            extra_headers={},  # 不注入 headers (由 proxy 层处理)
            metadata={
                "adapter": self.name,
                "note": "Using default adapter (minimal transformation)",
            },
        )
