"""
Codex Session 管理器

提供 conversation/session/prompt_cache 标识,按 24 小时轮换
"""
from __future__ import annotations

import time
import uuid
from threading import Lock
from typing import ClassVar, TypedDict


class SessionIdentifiers(TypedDict):
    """Codex 请求需要的标识集合"""

    conversation_id: str
    session_id: str
    prompt_cache_key: str


class CodexSessionManager:
    """
    Codex Session 管理器 (线程安全单例)

    - 24 小时 TTL
    - 同一窗口内复用 conversation/session/prompt_cache 标识
    """

    _instance: ClassVar[CodexSessionManager | None] = None
    _lock: ClassVar[Lock] = Lock()

    _ttl_seconds: int
    _cache: dict[str, dict[str, str | int]]

    def __new__(cls) -> CodexSessionManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._ttl_seconds = 24 * 3600  # 24 小时滚动窗口
                    cls._instance._cache = {}
        return cls._instance

    def get_identifiers(self) -> SessionIdentifiers:
        """
        获取当前窗口的标识集合

        Returns:
            SessionIdentifiers: conversation / session / prompt_cache_key
        """
        with self._lock:
            now = int(time.time())
            window = now // self._ttl_seconds
            cache_key = f"codex_session_{window}"

            cached = self._cache.get(cache_key)
            if cached and now - int(cached.get("created_at", 0)) < self._ttl_seconds:
                return SessionIdentifiers(
                    conversation_id=str(cached["conversation_id"]),
                    session_id=str(cached["session_id"]),
                    prompt_cache_key=str(cached["prompt_cache_key"]),
                )

            # 生成新的标识集合
            base_id = str(uuid.uuid4())
            identifiers = SessionIdentifiers(
                conversation_id=base_id,
                session_id=base_id,
                prompt_cache_key=base_id,
            )

            self._cache = {
                cache_key: {
                    **identifiers,
                    "created_at": now,
                }
            }

            return identifiers

    def clear_cache(self) -> None:
        """清空缓存 (测试用)"""
        with self._lock:
            self._cache = {}


# 全局单例
codex_session_manager = CodexSessionManager()

__all__ = ["codex_session_manager", "SessionIdentifiers"]

