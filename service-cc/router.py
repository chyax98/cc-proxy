"""
Claude Service FastAPI 路由
处理 Claude API 请求的路由和中间件
"""
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from common.adapters import AdapterContext
from common.config import settings
from common.errors import AuthenticationError, InvalidRequestError
from common.logger import get_logger

from .adapters.manager import adapter_manager
from .proxy import proxy_to_anthropic
from .schemas.base import ClaudeRequestBase

logger = get_logger(__name__)

router = APIRouter()


def extract_api_key(
    x_api_key: str | None = None,
    authorization: str | None = None,
) -> str:
    """
    从请求头提取 API Key

    Args:
        x_api_key: x-api-key 头
        authorization: Authorization 头

    Returns:
        API Key

    Raises:
        AuthenticationError: 未提供 API Key
    """
    # 优先使用 x-api-key
    if x_api_key:
        return x_api_key

    # 尝试从 Authorization 头提取
    if authorization:
        # 支持 "Bearer <key>" 和 "<key>" 两种格式
        if authorization.startswith("Bearer "):
            return authorization[7:]
        return authorization

    raise AuthenticationError("Missing API Key")


@router.post("/v1/messages")
async def create_message(
    request: Request,
    x_api_key: str | None = Header(None, alias="x-api-key"),
    authorization: str | None = Header(None),
) -> Any:
    """
    创建 Claude 消息

    Args:
        request: FastAPI 请求对象
        x_api_key: API Key (x-api-key 头)
        authorization: API Key (Authorization 头)

    Returns:
        Claude API 响应 (流式或非流式)

    Raises:
        HTTPException: 各种错误情况
    """
    try:
        # 1. 提取 API Key
        api_key = extract_api_key(x_api_key, authorization)

        # 2. 解析请求体
        body = await request.json()
        headers = dict(request.headers)

        # 记录请求信息 (根据环境决定是否记录详细内容)
        log_data = {
            "model": body.get("model"),
            "stream": body.get("stream", False),
            "message_count": len(body.get("messages", [])),
            "user_agent": headers.get("user-agent", "unknown"),
        }

        # 测试环境记录详细请求体
        if settings.is_test_environment:
            log_data["request_body"] = body

        logger.info("claude_request", **log_data)

        # 3. 验证请求体
        try:
            claude_request = ClaudeRequestBase(**body)
        except Exception as e:
            logger.error("request_validation_error", error=str(e))
            raise InvalidRequestError(
                f"Invalid request body: {e!s}",
                details={"validation_error": str(e)},
            ) from e

        # 4. 构建适配器上下文
        ctx = AdapterContext(
            raw_body=body,
            raw_headers=headers,
        )

        # 5. 应用适配器转换
        result = adapter_manager.transform(ctx)

        # 6. 代理到 Anthropic
        response = await proxy_to_anthropic(
            result.body,
            api_key,
            stream=claude_request.stream,
        )

        return response

    except AuthenticationError as e:
        logger.error("authentication_error", error=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e

    except InvalidRequestError as e:
        logger.error("invalid_request_error", error=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.to_dict()) from e

    except HTTPException:
        # FastAPI 异常直接抛出
        raise

    except Exception as e:
        logger.error(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "internal_error",
                    "message": "Internal server error",
                }
            },
        ) from e


@router.get("/adapters")
async def list_adapters() -> dict[str, list[dict[str, str | int]]]:
    """
    列出所有已注册的适配器

    Returns:
        适配器信息列表 (包含 name, version, priority)
    """
    adapters = adapter_manager.list_adapters()
    logger.info("adapters_listed", count=len(adapters))
    return {"adapters": adapters}
