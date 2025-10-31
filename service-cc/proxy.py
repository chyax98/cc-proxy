"""
Claude API 代理逻辑
负责转发请求到 Anthropic API
"""
from collections.abc import AsyncIterator

import httpx
from fastapi.responses import StreamingResponse

from common.config import settings
from common.errors import ServiceUnavailableError
from common.http_client import http_client
from common.logger import get_logger
from common.types import JSONData

from .formats.claude_code import build_claude_code_headers

logger = get_logger(__name__)


async def proxy_to_anthropic(
    body: JSONData,
    api_key: str,
    stream: bool = False,
) -> StreamingResponse | JSONData:
    """
    代理请求到 Anthropic API

    Args:
        body: 请求体 (已经过适配器转换)
        api_key: Anthropic API Key
        stream: 是否流式响应

    Returns:
        StreamingResponse (流式) 或 JSONData (非流式)

    Raises:
        ServiceUnavailableError: 服务不可用
        httpx.HTTPStatusError: HTTP 错误
    """
    url = f"{settings.anthropic_base_url}/v1/messages"
    headers = build_claude_code_headers(api_key)

    logger.info(
        "proxy_request_start",
        url=url,
        stream=stream,
        model=body.get("model"),
        message_count=len(body.get("messages", [])),
    )

    try:
        if stream:
            return StreamingResponse(
                _stream_anthropic_response(url, body, headers),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
                },
            )
        response = await http_client.request(
            "POST",
            url,
            json=body,
            headers=headers,
        )

        logger.info(
            "proxy_request_complete",
            status=response.status_code,
            response_size=len(response.content),
        )

        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(
            "anthropic_api_error",
            status=e.response.status_code,
            error=str(e),
            response_body=e.response.text[:500],  # 记录前 500 字符
        )
        raise

    except Exception as e:
        logger.error("proxy_error", error=str(e), error_type=type(e).__name__)
        raise ServiceUnavailableError("anthropic") from e


async def _stream_anthropic_response(
    url: str,
    body: JSONData,
    headers: dict[str, str],
) -> AsyncIterator[bytes]:
    """
    流式代理 Anthropic API 响应

    Args:
        url: API URL
        body: 请求体
        headers: 请求头

    Yields:
        SSE 事件数据块
    """
    chunk_count = 0
    try:
        async for chunk in http_client.stream_request(
            "POST",
            url,
            json=body,
            headers=headers,
        ):
            chunk_count += 1
            yield chunk

        logger.info("stream_complete", chunks=chunk_count)

    except httpx.HTTPStatusError as e:
        # HTTP 状态错误 (4xx, 5xx)
        logger.error(
            "stream_http_error",
            status=e.response.status_code,
            error=str(e),
            chunks_received=chunk_count,
        )
        # 发送 SSE 错误事件
        error_event = f'event: error\ndata: {{"error": "HTTP {e.response.status_code}: {e!s}"}}\n\n'
        yield error_event.encode("utf-8")

    except httpx.ReadTimeout as e:
        # 读取超时错误
        logger.error(
            "stream_timeout_error",
            error=str(e),
            chunks_received=chunk_count,
        )
        # 发送 SSE 错误事件
        error_event = 'event: error\ndata: {"error": "Stream read timeout"}\n\n'
        yield error_event.encode("utf-8")

    except httpx.NetworkError as e:
        # 网络错误
        logger.error(
            "stream_network_error",
            error=str(e),
            chunks_received=chunk_count,
        )
        # 发送 SSE 错误事件
        error_event = 'event: error\ndata: {"error": "Network error during streaming"}\n\n'
        yield error_event.encode("utf-8")

    except Exception as e:
        # 其他未预期的错误
        logger.error(
            "stream_error",
            error=str(e),
            error_type=type(e).__name__,
            chunks_received=chunk_count,
        )
        # 发送 SSE 错误事件
        error_event = 'event: error\ndata: {"error": "Stream interrupted unexpectedly"}\n\n'
        yield error_event.encode("utf-8")
