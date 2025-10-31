"""
CherryStudio 客户端适配器 (重构版)

使用转换管道架构，逻辑 100% 保留原实现
"""

from common.adapters import AdapterContext, ClientAdapter, TransformResult
from common.logger import get_logger
from common.transforms import TransformContext

from ..pipelines.cherry_studio import get_cherry_studio_pipeline

logger = get_logger(__name__)


class CherryStudioAdapter(ClientAdapter):
    """CherryStudio 客户端适配器"""

    name = "cherry_studio"
    priority = 50  # 中等优先级
    version = "3.0.0"  # 重构版本

    def __init__(self):
        """初始化适配器，获取预配置的转换管道"""
        self.pipeline = get_cherry_studio_pipeline()

    def detect(self, ctx: AdapterContext) -> bool:
        """
        检测是否为 CherryStudio 客户端

        检测规则: User-Agent 包含 "CherryStudio"

        逻辑 100% 保留原实现
        """
        # 检查 User-Agent
        user_agent = ctx.raw_headers.get("user-agent", "").lower()
        if "cherrystudio" in user_agent:
            logger.info("detected_cherry_studio", source="user_agent", user_agent=user_agent)
            return True

        logger.debug("not_cherry_studio", user_agent=user_agent)
        return False

    def transform(self, ctx: AdapterContext) -> TransformResult:
        """
        使用转换管道执行转换

        转换操作 (100% 保留原实现):
        1. 注入 Claude Code System 提示词
        2. 保留 thinking 字段 (透传给 88code)
        3. 添加 session metadata (12小时轮换)
        """
        # 构建转换上下文
        transform_ctx = TransformContext(
            target_api="claude",
            client_type="cherry_studio",
            raw_headers=ctx.raw_headers,
        )

        # 执行管道转换
        transformed_body = self.pipeline.execute(ctx.raw_body, transform_ctx)

        # 添加 cache_control 到最后一条 message content (Prompt Caching)
        # 这个逻辑不在 Transformer 中，因为它是 service-cc 特有的
        messages = transformed_body.get("messages", [])
        if messages and isinstance(messages[-1].get("content"), list):
            last_content = messages[-1]["content"]
            if last_content and isinstance(last_content[-1], dict):
                # 在最后一个 content block 添加 cache_control
                last_content[-1]["cache_control"] = {"type": "ephemeral"}
                logger.info(
                    "added_cache_control_to_last_message",
                    content_blocks=len(last_content),
                )

        # 记录转换完成
        thinking_enabled = "thinking" in transformed_body
        user_id = transformed_body.get("metadata", {}).get("user_id")

        logger.info(
            "transformed_request",
            adapter=self.name,
            system_blocks=len(transformed_body.get("system", [])),
            thinking_enabled=thinking_enabled,
            user_id=user_id,
        )

        return TransformResult(
            body=transformed_body,
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31",
            },
            metadata={
                "adapter": self.name,
                "version": self.version,
                "session_id": user_id,
                "thinking_enabled": thinking_enabled,
            },
        )
