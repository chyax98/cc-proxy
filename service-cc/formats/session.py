"""
Session 管理器
提供 12 小时轮换的 session ID 生成和缓存
"""
import time
from threading import Lock
from typing import ClassVar


class SessionManager:
    """Session 管理器 (单例,线程安全)"""

    _instance: ClassVar["SessionManager | None"] = None
    _lock: ClassVar[Lock] = Lock()
    _cache: dict[str, dict[str, int | str]]
    _ttl: int
    _counter: int

    def __new__(cls) -> "SessionManager":
        # 双重检查锁定 (Double-Checked Locking)
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._ttl = 12 * 3600  # 12 小时
                    cls._instance._counter = 0
        return cls._instance

    def get_session(self) -> dict[str, str]:
        """
        获取当前 session 信息 (线程安全)

        Returns:
            包含 user_id 的字典
        """
        # 使用锁保证原子性,避免竞态条件
        with self._lock:
            current_time = int(time.time())
            timestamp_12h = current_time // self._ttl

            cache_key = f"session_{timestamp_12h}"

            # 检查缓存是否过期
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if current_time - cached["created_at"] < self._ttl:
                    return {"user_id": str(cached["user_id"])}

            # 生成新 session (在锁内执行,保证 counter 递增原子性)
            self._counter += 1
            user_id = f"user_proxy_account__session_{timestamp_12h}-{self._counter}"

            # 更新缓存
            self._cache = {cache_key: {"user_id": user_id, "created_at": current_time}}

            return {"user_id": user_id}

    def clear_cache(self) -> None:
        """清空缓存 (测试用,线程安全)"""
        with self._lock:
            self._cache = {}
            self._counter = 0


# 全局 session 管理器实例
session_manager = SessionManager()
