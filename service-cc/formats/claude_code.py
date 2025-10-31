"""
Claude Code CLI 2.0.24 官方格式定义
包含 System 提示词和标准请求头
"""

# Claude Code 官方 System 提示词
CLAUDE_CODE_SYSTEM = [
    {
        "type": "text",
        "text": "You are Claude Code, Anthropic's official CLI for Claude.",
        "cache_control": {"type": "ephemeral"},
    }
]

# Claude Code 官方请求头
CLAUDE_CODE_HEADERS = {
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "claude-code-20250219",
    "user-agent": "claude-cli/2.0.24 (external, cli)",
}


def build_claude_code_headers(api_key: str) -> dict[str, str]:
    """
    构建 Claude Code 标准请求头

    Args:
        api_key: Anthropic API Key

    Returns:
        完整的请求头字典
    """
    return {
        **CLAUDE_CODE_HEADERS,
        "authorization": f"Bearer {api_key}",  # 88code 只需要 Authorization 头
        "content-type": "application/json",
    }
