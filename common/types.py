"""
通用类型定义
"""
from typing import Any, Literal

# 消息角色类型
MessageRole = Literal["user", "assistant", "system"]

# 内容类型
ContentType = Literal["text", "image", "tool_use", "tool_result"]

# HTTP 方法
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

# 服务类型
ServiceType = Literal["claude", "codex"]

# 请求头类型
Headers = dict[str, str]

# JSON 数据类型
JSONData = dict[str, Any]
