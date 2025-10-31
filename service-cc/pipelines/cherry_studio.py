"""
CherryStudio 客户端的转换管道配置

转换流程: CherryStudio → Claude API
"""

from common.transforms import (
    FieldResolverTransformer,
    SessionTransformer,
    SystemPromptTransformer,
    TransformPipeline,
)

from ..formats.claude_code import CLAUDE_CODE_SYSTEM
from ..formats.session import session_manager


def get_cherry_studio_pipeline() -> TransformPipeline:
    """
    获取 CherryStudio → Claude API 的转换管道

    转换步骤:
    1. SystemPromptTransformer - 注入 Claude Code system prompt
    2. FieldResolverTransformer - 解析字段 (thinking 字段会自动保留)
    3. SessionTransformer - 添加 12 小时 session

    逻辑 100% 保留原有实现:
    - 注入 CLAUDE_CODE_SYSTEM (列表格式)
    - 保留 thinking 字段 (不移除)
    - 添加 12 小时轮换的 session metadata
    """
    return TransformPipeline(
        [
            # 1. 注入 Claude Code system prompt
            SystemPromptTransformer(CLAUDE_CODE_SYSTEM),
            # 2. 解析字段 (thinking 会自动保留，因为没有 Transformer 删除它)
            FieldResolverTransformer(),
            # 3. 添加 12 小时 session
            SessionTransformer(session_manager),
        ]
    )


__all__ = ["get_cherry_studio_pipeline"]
