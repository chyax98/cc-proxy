"""
HTTP 客户端
使用 httpx 提供异步 HTTP 客户端,支持 HTTP/2 和连接池
"""
from collections.abc import AsyncIterator
from threading import Lock
from typing import Any

import httpx

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """异步 HTTP 客户端 (单例,线程安全)"""

    _instance: "HTTPClient | None" = None
    _client: httpx.AsyncClient | None = None
    _lock = Lock()

    def __new__(cls) -> "HTTPClient":
        # 双重检查锁定
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._client is None:
            self._client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        """创建 HTTP 客户端实例"""
        return httpx.AsyncClient(
            http2=True,  # 启用 HTTP/2
            limits=httpx.Limits(
                max_keepalive_connections=settings.http_max_keepalive,
                max_connections=settings.http_max_connections,
                keepalive_expiry=settings.http_keepalive_expiry,
            ),
            timeout=httpx.Timeout(
                timeout=settings.http_timeout,
                connect=settings.http_connect_timeout,
            ),
            follow_redirects=False,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        """获取客户端实例"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    async def stream_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """流式请求"""
        logger.info("stream_request_start", method=method, url=url)

        try:
            async with self.client.stream(method, url, **kwargs) as response:
                response.raise_for_status()

                chunk_count = 0
                async for chunk in response.aiter_bytes():
                    chunk_count += 1
                    yield chunk

                logger.info(
                    "stream_request_complete",
                    method=method,
                    url=url,
                    chunks=chunk_count,
                    status=response.status_code,
                )

        except httpx.HTTPStatusError as e:
            logger.error(
                "stream_request_http_error",
                method=method,
                url=url,
                status=e.response.status_code,
                error=str(e),
            )
            raise

        except Exception as e:
            logger.error("stream_request_error", method=method, url=url, error=str(e))
            raise

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """普通请求"""
        logger.info("request_start", method=method, url=url)

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()

            logger.info(
                "request_complete",
                method=method,
                url=url,
                status=response.status_code,
            )

            return response

        except httpx.HTTPStatusError as e:
            logger.error(
                "request_http_error",
                method=method,
                url=url,
                status=e.response.status_code,
                error=str(e),
            )
            raise

        except Exception as e:
            logger.error("request_error", method=method, url=url, error=str(e))
            raise

    async def close(self) -> None:
        """关闭客户端 (线程安全)"""
        with self._lock:
            if self._client is not None:
                await self._client.aclose()
                self._client = None
                logger.info("http_client_closed")

    @classmethod
    def reset_instance(cls) -> None:
        """
        重置单例实例 (测试用)
        注意: 需要先调用 close() 关闭客户端
        """
        with cls._lock:
            cls._instance = None
            logger.info("http_client_instance_reset")

    def __del__(self) -> None:
        """析构函数,确保客户端被关闭"""
        # 注意: 在析构函数中不能使用 await,只能记录警告
        if self._client is not None and not self._client.is_closed:
            logger.warning(
                "http_client_not_closed",
                message="HTTPClient was not properly closed before deletion",
            )


# 全局 HTTP 客户端实例
http_client = HTTPClient()
