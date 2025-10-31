"""
自定义异常类
"""
from typing import Any


class ProxyError(Exception):
    """代理错误基类"""

    def __init__(
        self,
        message: str,
        error_type: str = "proxy_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                **self.details,
            }
        }


class AuthenticationError(ProxyError):
    """认证错误"""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message=message,
            error_type="authentication_error",
            status_code=401,
        )


class InvalidRequestError(ProxyError):
    """无效请求错误"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_type="invalid_request_error",
            status_code=400,
            details=details,
        )


class ServiceUnavailableError(ProxyError):
    """服务不可用错误"""

    def __init__(self, service: str) -> None:
        super().__init__(
            message=f"Service '{service}' is unavailable",
            error_type="service_unavailable",
            status_code=503,
            details={"service": service},
        )
