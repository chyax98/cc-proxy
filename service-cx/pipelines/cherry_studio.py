"""
CherryStudio 客户端的转换管道配置

转换流程: CherryStudio → OpenAI Codex API
"""

from common.transforms import (
    EnvironmentContextTransformer,
    FieldResolverTransformer,
    MessageNormalizerTransformer,
    SessionTransformer,
    SystemPromptTransformer,
    ToolsMergerTransformer,
    TransformPipeline,
)

from ..formats.codex_instructions import CODEX_INSTRUCTIONS
from ..formats.codex_tools import CODEX_DEFAULT_TOOLS
from ..formats.session import codex_session_manager


def get_cherry_studio_pipeline() -> TransformPipeline:
    """
    获取 CherryStudio → OpenAI Codex API 的转换管道

    转换步骤:
    1. SystemPromptTransformer - 注入 Codex instructions
    2. MessageNormalizerTransformer - 标准化消息格式
    3. ToolsMergerTransformer - 合并默认工具和客户端工具
    4. FieldResolverTransformer - 解析字段 (tool_choice, reasoning, include)
    5. SessionTransformer - 添加 24 小时 session
    6. EnvironmentContextTransformer - 添加环境上下文 (cwd)

    逻辑 100% 保留原有实现:
    - 注入 CODEX_INSTRUCTIONS (字符串格式)
    - 标准化消息格式 (input→messages)
    - 合并 7 个默认工具 + 客户端工具
    - 解析 tool_choice, parallel_tool_calls, reasoning, include
    - 添加 24 小时轮换的 session
    - 添加环境上下文 (cwd, 88code-specific)
    """
    return TransformPipeline(
        [
            # 1. 注入 Codex instructions
            SystemPromptTransformer(CODEX_INSTRUCTIONS),
            # 2. 标准化消息格式 (input → messages)
            MessageNormalizerTransformer(),
            # 3. 合并默认工具
            ToolsMergerTransformer(CODEX_DEFAULT_TOOLS),
            # 4. 解析字段
            FieldResolverTransformer(),
            # 5. 添加 24 小时 session
            SessionTransformer(codex_session_manager),
            # 6. 添加环境上下文
            EnvironmentContextTransformer(),
        ]
    )


__all__ = ["get_cherry_studio_pipeline"]
