"""
Session 转换器

负责添加 Session/Conversation 标识
"""

from __future__ import annotations

from typing import Any

from .base import TransformContext, Transformer


class SessionTransformer(Transformer):
    """
    Session 转换器

    根据目标 API 类型添加不同的 session 标识:
    - Claude API: metadata.user_id (12 小时轮换)
    - OpenAI API: conversation_id, session_id, prompt_cache_key (24 小时轮换)

    逻辑 100% 保留原实现
    """

    name = "session"

    def __init__(self, session_manager: Any):
        """
        初始化转换器

        Args:
            session_manager: Session 管理器
                - Claude: SessionManager (get_session())
                - OpenAI: CodexSessionManager (get_identifiers())
        """
        self.session_manager = session_manager

    def transform(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        添加 Session 标识

        逻辑 100% 保留原实现
        """
        if context.target_api == "claude":
            # Claude API: metadata.user_id
            session = self.session_manager.get_session()
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["user_id"] = session["user_id"]

        elif context.target_api == "openai":
            # OpenAI API: conversation_id, session_id, prompt_cache_key
            identifiers = self.session_manager.get_identifiers()
            data["prompt_cache_key"] = identifiers["prompt_cache_key"]

            # 将 identifiers 存储到 context.metadata 供后续使用
            context.metadata["conversation_id"] = identifiers["conversation_id"]
            context.metadata["session_id"] = identifiers["session_id"]

        return data


__all__ = ["SessionTransformer"]
