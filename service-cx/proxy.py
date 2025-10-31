"""
Codex 服务代理转发逻辑
负责将请求转发到 OpenAI Responses API
"""
import json
import time
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx

from common.config import settings
from common.errors import InvalidRequestError, ServiceUnavailableError
from common.http_client import http_client
from common.logger import get_logger
from common.types import JSONData

from .formats import build_responses_headers, parse_response

logger = get_logger(__name__)


def _maybe_dump_request(stage: str, body: JSONData, headers: dict[str, str]) -> None:
    """根据配置将请求写入本地文件,便于分析"""
    if not settings.codex_dump_requests:
        return

    try:
        dump_dir = Path(settings.codex_dump_dir)
        dump_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = dump_dir / f"codex_{stage}_{timestamp}_{uuid4().hex}.json"

        with file_path.open("w", encoding="utf-8") as fp:
            json.dump(
                {
                    "stage": stage,
                    "timestamp": timestamp,
                    "headers": headers,
                    "body": body,
                },
                fp,
                ensure_ascii=False,
                indent=2,
            )

        logger.info("codex_request_dumped", stage=stage, path=str(file_path))
    except Exception as err:
        logger.warning("codex_request_dump_failed", stage=stage, error=str(err))


async def proxy_to_openai(
    body: JSONData,
    api_key: str,
    extra_headers: dict[str, str] | None = None,
) -> JSONData:
    """
    代理请求到 OpenAI Responses API

    Args:
        body: 请求体（已转换为 Responses API 格式）
        api_key: OpenAI API Key
        extra_headers: 需要附加到请求的头部信息

    Returns:
        JSONData: OpenAI API 响应

    Raises:
        InvalidRequestError: 请求参数无效
        ServiceUnavailableError: OpenAI 服务不可用
    """
    url = f"{settings.openai_base_url}/v1/responses"

    logger.info(
        "proxy_request_start",
        url=url,
        model=body.get("model"),
        tool_choice=body.get("tool_choice"),
        stream=bool(body.get("stream")),
        has_instructions=bool(body.get("instructions")),
        instructions_length=len(body.get("instructions", "")) if body.get("instructions") else 0,
    )

    # 调试: 打印完整请求体 (截取 instructions 前 100 字符)
    debug_body = body.copy()
    if "instructions" in debug_body and len(str(debug_body["instructions"])) > 100:
        debug_body["instructions"] = str(debug_body["instructions"])[:100] + "..."
    logger.debug("proxy_request_body", body=debug_body)

    try:
        # 构建请求头
        headers = build_responses_headers(api_key, extra_headers)
        _maybe_dump_request("request", body, headers)

        # 发送请求
        response = await http_client.request(
            "POST",
            url,
            json=body,
            headers=headers,
        )

        # 记录原始响应内容用于调试
        response_text = response.text
        logger.debug(
            "proxy_response_raw",
            status=response.status_code,
            content_type=response.headers.get("content-type"),
            body_preview=response_text[:500] if response_text else "(empty)",
        )

        # 解析响应
        if not response_text:
            raise InvalidRequestError(
                message="API returned empty response",
                details={"status_code": response.status_code},
            )

        try:
            response_data = response.json()
        except Exception as e:
            logger.error(
                "proxy_response_parse_error",
                status=response.status_code,
                error=str(e),
                body=response_text[:1000],
            )
            raise InvalidRequestError(
                message=f"Failed to parse API response: {e!s}",
                details={"response_text": response_text[:500]},
            ) from e

        parsed_response = parse_response(response_data)
        _maybe_dump_request("response", parsed_response, dict(response.headers))

        logger.info(
            "proxy_request_success",
            response_id=parsed_response.get("id"),
            status=parsed_response.get("status"),
            output_count=len(parsed_response.get("output", [])),
        )

        return parsed_response

    except httpx.HTTPStatusError as e:
        # HTTP 错误处理
        status_code = e.response.status_code
        error_body = {}

        try:
            error_body = e.response.json()
        except Exception:
            error_body = {"message": e.response.text}

        logger.error(
            "proxy_request_http_error",
            status_code=status_code,
            error=error_body,
        )

        # 根据状态码抛出不同错误
        if status_code == 400:
            raise InvalidRequestError(
                message=error_body.get("error", {}).get("message", "Invalid request"),
                details=error_body,
            ) from e
        if status_code in (503, 502, 504):
            raise ServiceUnavailableError("openai") from e
        raise InvalidRequestError(
            message=f"OpenAI API error: {status_code}",
            details=error_body,
        ) from e

    except httpx.RequestError as e:
        # 网络错误
        logger.error(
            "proxy_request_network_error",
            url=url,
            error=str(e),
        )
        raise ServiceUnavailableError("openai") from e

    except Exception as e:
        # 其他错误
        logger.error(
            "proxy_request_unexpected_error",
            url=url,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise InvalidRequestError(
            message=f"Unexpected error: {e!s}",
            details={"error_type": type(e).__name__},
        ) from e


async def proxy_to_openai_stream(
    body: JSONData,
    api_key: str,
    extra_headers: dict[str, str] | None = None,
) -> tuple[AsyncIterator[bytes], dict[str, str], str]:
    """
    以流式方式代理请求到 OpenAI Responses API

    Args:
        body: 请求体（已转换为 Responses API 格式）
        api_key: OpenAI API Key
        extra_headers: 需要附加到请求的头部信息

    Returns:
        tuple: (异步字节迭代器, 需要透传的响应头, 响应媒体类型)

    Raises:
        InvalidRequestError: 请求参数无效
        ServiceUnavailableError: OpenAI 服务不可用
    """
    url = f"{settings.openai_base_url}/v1/responses"

    logger.info(
        "proxy_stream_request_start",
        url=url,
        model=body.get("model"),
        tool_choice=body.get("tool_choice"),
    )

    headers = build_responses_headers(api_key, extra_headers)

    stream_context = http_client.client.stream(
        "POST",
        url,
        json=body,
        headers=headers,
    )

    try:
        response = await stream_context.__aenter__()
    except httpx.RequestError as e:
        await stream_context.__aexit__(type(e), e, e.__traceback__)
        logger.error(
            "proxy_stream_connection_error",
            url=url,
            error=str(e),
        )
        raise ServiceUnavailableError("openai") from e
    except Exception as e:
        await stream_context.__aexit__(type(e), e, e.__traceback__)
        logger.error(
            "proxy_stream_unexpected_error",
            url=url,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise InvalidRequestError(
            message=f"Unexpected error: {e!s}",
            details={"error_type": type(e).__name__},
        ) from e

    content_type = response.headers.get("content-type", "text/event-stream; charset=utf-8")
    request_id = response.headers.get("x-request-id")
    status_code = response.status_code

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        error_bytes = await response.aread()
        error_text = error_bytes.decode("utf-8", errors="ignore")
        await stream_context.__aexit__(type(e), e, e.__traceback__)

        if status_code == 400:
            raise InvalidRequestError(
                message="Invalid streaming request",
                details={"response": error_text[:500]},
            ) from e
        if status_code in (503, 502, 504):
            raise ServiceUnavailableError("openai") from e
        raise InvalidRequestError(
            message=f"OpenAI streaming error: {status_code}",
            details={"response": error_text[:500]},
        ) from e

    passthrough_headers: dict[str, str] = {}
    if request_id:
        passthrough_headers["x-request-id"] = request_id
    cache_control = response.headers.get("cache-control")
    if cache_control:
        passthrough_headers["cache-control"] = cache_control

    _maybe_dump_request(
        "stream_response_headers",
        {"status": status_code},
        dict(response.headers),
    )

    async def stream_iterator() -> AsyncIterator[bytes]:
        chunk_count = 0
        try:
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunk_count += 1
                    yield chunk
        except httpx.ReadTimeout as e:
            # 读取超时错误
            logger.error(
                "proxy_stream_timeout_error",
                error=str(e),
                chunks_received=chunk_count,
            )
            # 发送 SSE 错误事件
            error_event = 'event: error\ndata: {"error": "Stream read timeout"}\n\n'
            yield error_event.encode("utf-8")
        except httpx.NetworkError as e:
            # 网络错误
            logger.error(
                "proxy_stream_network_error",
                error=str(e),
                chunks_received=chunk_count,
            )
            # 发送 SSE 错误事件
            error_event = 'event: error\ndata: {"error": "Network error during streaming"}\n\n'
            yield error_event.encode("utf-8")
        except Exception as e:
            # 其他未预期的错误
            logger.error(
                "proxy_stream_forward_error",
                error=str(e),
                error_type=type(e).__name__,
                chunks_received=chunk_count,
            )
            # 发送 SSE 错误事件
            error_event = 'event: error\ndata: {"error": "Stream interrupted unexpectedly"}\n\n'
            yield error_event.encode("utf-8")
        finally:
            await stream_context.__aexit__(None, None, None)
            logger.info(
                "proxy_stream_request_complete",
                status=status_code,
                chunks=chunk_count,
            )

    return stream_iterator(), passthrough_headers, content_type


async def validate_request_body(body: JSONData) -> None:
    """
    验证请求体格式并规范化参数

    Args:
        body: 请求体

    Raises:
        InvalidRequestError: 请求体格式无效
    """
    # 检查必需字段
    if "model" not in body:
        raise InvalidRequestError(
            message="Missing required field: model",
            details={"field": "model"},
        )

    if "input" not in body:
        raise InvalidRequestError(
            message="Missing required field: input",
            details={"field": "input"},
        )

    # 验证字段类型
    if not isinstance(body["model"], str):
        raise InvalidRequestError(
            message="Field 'model' must be a string",
            details={"field": "model", "type": type(body["model"]).__name__},
        )

    input_data = body["input"]
    if not isinstance(input_data, (str, list)):
        raise InvalidRequestError(
            message="Field 'input' must be a string or array",
            details={"field": "input", "type": type(input_data).__name__},
        )

    stream_value = body.get("stream")
    if stream_value is not None and not isinstance(stream_value, bool):
        raise InvalidRequestError(
            message="Field 'stream' must be a boolean when provided",
            details={"field": "stream", "type": type(stream_value).__name__},
        )

    logger.debug(
        "request_body_validated",
        model=body["model"],
        stream_enabled=bool(stream_value),
    )
