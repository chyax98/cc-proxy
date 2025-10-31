"""
Codex 环境上下文消息构建
"""
from __future__ import annotations

from common.config import settings


def build_environment_context_message() -> dict[str, object]:
    """构建 Codex CLI 默认为首条输入的环境上下文消息"""
    text = (
        "<environment_context>\n"
        f"  <cwd>{settings.codex_env_cwd}</cwd>\n"
        f"  <approval_policy>{settings.codex_env_approval_policy}</approval_policy>\n"
        f"  <sandbox_mode>{settings.codex_env_sandbox_mode}</sandbox_mode>\n"
        f"  <network_access>{settings.codex_env_network_access}</network_access>\n"
        f"  <shell>{settings.codex_env_shell}</shell>\n"
        "</environment_context>"
    )

    return {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": text,
            }
        ],
    }


def has_environment_context(messages: list[dict[str, object]]) -> bool:
    """检测消息数组中是否已包含环境上下文"""
    for msg in messages:
        contents = msg.get("content")
        if isinstance(contents, list):
            for block in contents:
                if isinstance(block, dict) and block.get("type") == "input_text":
                    text = block.get("text")
                    if isinstance(text, str) and "<environment_context>" in text:
                        return True
    return False


__all__ = ["build_environment_context_message", "has_environment_context"]

