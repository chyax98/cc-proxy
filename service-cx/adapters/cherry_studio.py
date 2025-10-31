"""
CherryStudio 客户端适配器 (重构版)

使用转换管道架构,逻辑 100% 保留原实现
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
        """初始化适配器,获取预配置的转换管道"""
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
        1. 注入 Codex instructions
        2. 标准化消息格式 (input → messages)
        3. 合并默认工具 (7 个 Codex 工具)
        4. 解析字段 (tool_choice, reasoning, include)
        5. 添加 24 小时 session
        6. 添加环境上下文 (cwd)
        """
        # 构建转换上下文
        transform_ctx = TransformContext(
            target_api="openai",
            client_type="cherry_studio",
            raw_headers=ctx.raw_headers,
        )

        # 执行管道转换
        transformed_body = self.pipeline.execute(ctx.raw_body, transform_ctx)

        # 记录转换完成
        reasoning_enabled = "reasoning" in transformed_body
        conversation_id = transform_ctx.metadata.get("conversation_id")

        logger.info(
            "transformed_request",
            adapter=self.name,
            message_count=len(transformed_body.get("messages", [])),
            tools_count=len(transformed_body.get("tools", [])),
            reasoning_enabled=reasoning_enabled,
            conversation_id=conversation_id,
        )

        return TransformResult(
            body=transformed_body,
            extra_headers={},
            metadata={
                "adapter": self.name,
                "version": self.version,
                "conversation_id": conversation_id,
                "session_id": transform_ctx.metadata.get("session_id"),
                "reasoning_enabled": reasoning_enabled,
            },
        )
