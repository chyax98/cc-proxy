"""
OpenAI Responses API 格式定义
定义请求头、响应头和数据转换规则
"""
from typing import Any


def build_responses_headers(
    api_key: str,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    构建 OpenAI Responses API 请求头

    模拟真实的 Codex CLI 请求头

    Args:
        api_key: OpenAI API Key (88code 的)

    Returns:
        dict[str, str]: 请求头字典
    """
    headers = {
        "authorization": f"Bearer {api_key}",
        "openai-beta": "responses=experimental",
        "accept": "text/event-stream",
        "codex-task-type": "standard",
        "content-type": "application/json",
        "user-agent": "codex_cli_rs/0.50.0 (Mac OS 26.0.1; arm64) ghostty/1.2.2",
        "originator": "codex_cli_rs",
    }

    if extra_headers:
        headers.update(extra_headers)

    return headers


def format_input(input_data: list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    """
    格式化输入数据

    Args:
        {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "测试"
            }
        ]
    }
        input_data: 原始输入数据

    Returns:
        格式化后的输入数据
    """
    if len(input_data) == 0:
        return input_data
    for input_item in input_data:
        if input_item.get("role") == "developer":
            input_item["role"] = "user"


    # 如果是消息数组，确保格式正确
    if isinstance(input_data, list):
        formatted_messages = []
        for msg in input_data:
            if isinstance(msg, dict):
                # 确保消息包含必需字段
                formatted_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                }
                # 保留其他字段
                for key, value in msg.items():
                    if key not in ["role", "content"]:
                        formatted_msg[key] = value
                formatted_messages.append(formatted_msg)
        return formatted_messages

    # 其他情况转换为字符串
    return str(input_data)


def build_request_body(
    model: str,
    input_data: str | list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    构建 OpenAI Responses API 请求体

    Args:
        model: 模型名称
        input_data: 输入内容
        tools: 工具列表
        temperature: 温度参数
        max_output_tokens: 最大输出 token 数
        metadata: 元数据

    Returns:
        dict[str, Any]: 请求体字典
    """
    body: dict[str, Any] = {
        "model": model,
        "input": format_input(input_data),
    }

    # 添加可选参数
    if tools is not None:
        body["tools"] = tools

    if temperature is not None:
        body["temperature"] = temperature

    if max_output_tokens is not None:
        body["max_output_tokens"] = max_output_tokens

    if metadata is not None:
        body["metadata"] = metadata

    return body


def parse_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """
    解析 OpenAI Responses API 响应

    Args:
        response_data: 原始响应数据

    Returns:
        dict[str, Any]: 解析后的响应数据
    """
    # 确保响应包含必需字段
    parsed = {
        "id": response_data.get("id", ""),
        "object": response_data.get("object", "response"),
        "created_at": response_data.get("created_at", 0),
        "status": response_data.get("status", "completed"),
        "output": response_data.get("output", []),
        "usage": response_data.get("usage", {}),
    }

    # 保留其他字段
    for key, value in response_data.items():
        if key not in parsed:
            parsed[key] = value

    return parsed
