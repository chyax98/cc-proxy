"""
Codex CLI 默认工具定义

从真实 codex_cli_rs 请求中提取的工具描述,必须与官方结构保持一致
"""

from __future__ import annotations

from typing import Any

# Codex CLI 默认内置工具 (保持与官方 CLI 完全一致)
CODEX_DEFAULT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "shell",
        "description": "Runs a shell command and returns its output.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The command to execute",
                },
                "justification": {
                    "type": "string",
                    "description": (
                        "Only set if with_escalated_permissions is true. "
                        "1-sentence explanation of why we want to run this command."
                    ),
                },
                "timeout_ms": {
                    "type": "number",
                    "description": "The timeout for the command in milliseconds",
                },
                "with_escalated_permissions": {
                    "type": "boolean",
                    "description": (
                        "Whether to request escalated permissions. "
                        "Set to true if command needs to be run without sandbox restrictions"
                    ),
                },
                "workdir": {
                    "type": "string",
                    "description": "The working directory to execute the command in",
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_mcp_resources",
        "description": (
            "Lists resources provided by MCP servers. Resources allow servers to share data that "
            "provides context to language models, such as files, database schemas, or "
            "application-specific information. Prefer resources over web search when possible."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "cursor": {
                    "type": "string",
                    "description": (
                        "Opaque cursor returned by a previous list_mcp_resources call for the same server."
                    ),
                },
                "server": {
                    "type": "string",
                    "description": (
                        "Optional MCP server name. When omitted, lists resources from every configured server."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_mcp_resource_templates",
        "description": (
            "Lists resource templates provided by MCP servers. Parameterized resource templates allow "
            "servers to share data that takes parameters and provides context to language models, "
            "such as files, database schemas, or application-specific information. "
            "Prefer resource templates over web search when possible."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "cursor": {
                    "type": "string",
                    "description": (
                        "Opaque cursor returned by a previous list_mcp_resource_templates call for the same server."
                    ),
                },
                "server": {
                    "type": "string",
                    "description": (
                        "Optional MCP server name. When omitted, lists resource templates from all configured servers."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_mcp_resource",
        "description": (
            "Read a specific resource from an MCP server given the server name and resource URI."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": (
                        "MCP server name exactly as configured. Must match the 'server' field returned by list_mcp_resources."
                    ),
                },
                "uri": {
                    "type": "string",
                    "description": (
                        "Resource URI to read. Must be one of the URIs returned by list_mcp_resources."
                    ),
                },
            },
            "required": ["server", "uri"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "update_plan",
        "description": (
            "Updates the task plan.\nProvide an optional explanation and a list of plan items, each with a step "
            "and status.\nAt most one step can be in_progress at a time.\n"
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {"type": "string"},
                "plan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "One of: pending, in_progress, completed",
                            },
                            "step": {"type": "string"},
                        },
                        "required": ["step", "status"],
                        "additionalProperties": False,
                    },
                    "description": "The list of steps",
                },
            },
            "required": ["plan"],
            "additionalProperties": False,
        },
    },
    {
        "type": "custom",
        "name": "apply_patch",
        "description": (
            "Use the `apply_patch` tool to edit files. This is a FREEFORM tool, so do not wrap the patch in JSON."
        ),
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": (
                "start: begin_patch hunk+ end_patch\n"
                "begin_patch: \"*** Begin Patch\" LF\n"
                "end_patch: \"*** End Patch\" LF?\n\n"
                "hunk: add_hunk | delete_hunk | update_hunk\n"
                "add_hunk: \"*** Add File: \" filename LF add_line+\n"
                "delete_hunk: \"*** Delete File: \" filename LF\n"
                "update_hunk: \"*** Update File: \" filename LF change_move? change?\n\n"
                "filename: /(.+)/\n"
                "add_line: \"+\" /(.*)/ LF -> line\n\n"
                "change_move: \"*** Move to: \" filename LF\n"
                "change: (change_context | change_line)+ eof_line?\n"
                "change_context: (\"@@\" | \"@@ \" /(.+)/) LF\n"
                "change_line: (\"+\" | \"-\" | \" \") /(.*)/ LF\n"
                "eof_line: \"*** End of File\" LF\n\n"
                "%import common.LF\n"
            ),
        },
    },
    {
        "type": "function",
        "name": "view_image",
        "description": "Attach a local image (by filesystem path) to the conversation context for this turn.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Local filesystem path to an image file",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
]

__all__ = ["CODEX_DEFAULT_TOOLS"]

