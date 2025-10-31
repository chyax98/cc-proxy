"""
Claude Code CLI 客户端适配器

检测官方 Claude Code CLI 并直接透传请求
使用统一的 common.adapters 接口
"""

from common.adapters import AdapterContext, ClientAdapter, TransformResult
from common.logger import get_logger

logger = get_logger(__name__)


class ClaudeCodeAdapter(ClientAdapter):
    """Claude Code CLI 客户端适配器"""

    name = "claude_code"
    priority = 100  # 最高优先级 (官方客户端)
    version = "1.0.0"

    def detect(self, ctx: AdapterContext) -> bool:
        """
        检测是否为 Claude Code CLI

        检测规则:
        1. User-Agent 包含 "claude-cli"
        2. 或者包含 "anthropic-beta: claude-code-"

        Args:
            ctx: 适配器上下文

        Returns:
            是否为 Claude Code CLI
        """
        # 检查 User-Agent
        user_agent = ctx.raw_headers.get("user-agent", "").lower()
        if "claude-cli" in user_agent:
            logger.info("detected_claude_code", source="user_agent", user_agent=user_agent)
            return True

        # 检查 anthropic-beta 头
        anthropic_beta = ctx.raw_headers.get("anthropic-beta", "").lower()
        if "claude-code-" in anthropic_beta:
            logger.info("detected_claude_code", source="anthropic_beta", beta=anthropic_beta)
            return True

        logger.debug("not_claude_code", user_agent=user_agent)
        return False

    def transform(self, ctx: AdapterContext) -> TransformResult:
        """
        转换 Claude Code CLI 请求

        Claude Code CLI 的请求已经是完整格式,直接透传即可。
        不做任何修改,保留所有字段 (system, tools, thinking, metadata 等)

        Args:
            ctx: 适配器上下文

        Returns:
            转换结果 (直接透传原始请求体)
        """
        body = ctx.raw_body  # 直接使用原始请求,不做任何修改

        # 记录请求信息 (仅用于调试)
        thinking_enabled = "thinking" in body
        has_metadata = "metadata" in body

        logger.info(
            "claude_code_passthrough",
            adapter=self.name,
            system_blocks=len(body.get("system", [])),
            tools_count=len(body.get("tools", [])),
            thinking_enabled=thinking_enabled,
            has_metadata=has_metadata,
            user_id=body.get("metadata", {}).get("user_id") if has_metadata else None,
        )

        return TransformResult(
            body=body,  # 完全透传
            extra_headers={},  # 不注入任何额外 headers
            metadata={
                "adapter": self.name,
                "version": self.version,
                "is_official_client": True,
                "passthrough": True,  # 标记为透传模式
            },
        )
