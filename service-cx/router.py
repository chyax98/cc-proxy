"""
Codex 服务路由
定义 API 端点和请求处理逻辑
"""
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from common.adapters import AdapterContext
from common.errors import AuthenticationError, InvalidRequestError, ProxyError
from common.logger import get_logger

from .adapters import adapter_manager
from .proxy import proxy_to_openai, proxy_to_openai_stream, validate_request_body

logger = get_logger(__name__)

router = APIRouter()


def extract_api_key(authorization: str | None) -> str:
    """
    从 Authorization header 提取 API Key

    Args:
        authorization: Authorization header 值

    Returns:
        str: API Key

    Raises:
        AuthenticationError: API Key 无效或缺失
    """
    if not authorization:
        raise AuthenticationError("Missing Authorization header")

    # 支持 "Bearer xxx" 格式
    if authorization.startswith("Bearer "):
        api_key = authorization[7:].strip()
        if api_key:
            return api_key

    # 支持直接传递 API Key
    if authorization.strip():
        return authorization.strip()

    raise AuthenticationError("Invalid Authorization header format")


@router.post("/v1/responses")
async def create_response(
    request: Request,
    authorization: str | None = Header(None),
) -> Response:
    """
    创建响应（OpenAI Responses API）

    Args:
        request: FastAPI Request 对象
        authorization: Authorization header

    Returns:
        JSONResponse: OpenAI API 响应

    Raises:
        HTTPException: 各种错误情况
    """
    try:
        # 1. 提取 API Key
        api_key = extract_api_key(authorization)

        # 2. 解析请求体
        body = await request.json()
        headers = {k.lower(): v for k, v in request.headers.items()}

        # 3. 适配器转换
        ctx = AdapterContext(raw_body=body, raw_headers=headers)
        result = adapter_manager.transform(ctx)
        transformed_body = result.body
        extra_headers = result.extra_headers

        # 4. 验证请求体
        await validate_request_body(transformed_body)

        # 5. 代理转发到真实 API
        if bool(transformed_body.get("stream")):
            stream_iterator, passthrough_headers, media_type = await proxy_to_openai_stream(
                transformed_body,
                api_key,
                extra_headers,
            )

            headers = {
                "cache-control": "no-cache",
                "connection": "keep-alive",
                "x-accel-buffering": "no",
            }
            headers.update(passthrough_headers)

            return StreamingResponse(
                stream_iterator,
                media_type=media_type or "text/event-stream; charset=utf-8",
                headers=headers,
                status_code=status.HTTP_200_OK,
            )

        response_data = await proxy_to_openai(transformed_body, api_key, extra_headers)

        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_200_OK,
        )

    except AuthenticationError as e:
        logger.warning(
            "authentication_error",
            error=e.message,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict(),
        ) from e

    except InvalidRequestError as e:
        logger.warning(
            "invalid_request_error",
            error=e.message,
            details=e.details,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict(),
        ) from e

    except ProxyError as e:
        logger.error(
            "proxy_error",
            error_type=e.error_type,
            error=e.message,
            details=e.details,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict(),
        ) from e

    except Exception as e:
        logger.error(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "internal_error",
                    "message": "An unexpected error occurred",
                }
            },
        ) from e


@router.get("/v1")
async def api_info() -> dict[str, Any]:
    """
    API 信息端点 (CherryStudio 验证用)

    Returns:
        dict[str, Any]: API 信息
    """
    return {
        "api": "responses",
        "version": "v1",
        "supported": True,
    }


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    健康检查端点

    Returns:
        dict[str, Any]: 健康状态
    """
    return {
        "status": "healthy",
        "service": "codex",
        "version": "1.0.0",
    }
