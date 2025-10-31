# 需求：
cx-proxy实现cherry studio的 v1/response请求转换为标准 OpenAI v1/response请求（codex标准形式）
通过代理实现，要求架构合理，处理的性能损耗在50-200ms

## cherry studio的 v1/response
### 请求头：
```json
{
  "host": "localhost:9999",
  "connection": "keep-alive",
  "content-length": "5739",
  "sec-ch-ua-platform": "\"macOS\"",
  "authorization": "Bearer 88_5cd1b631293bad107424b5e9954d278e623b4d1a9455a879883deaeff3c5185e",
  "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\"",
  "sec-ch-ua-mobile": "?0",
  "x-title": "Cherry Studio",
  "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.6.5 Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36",
  "http-referer": "https://cherry-ai.com",
  "content-type": "application/json",
  "accept": "*/*",
  "sec-fetch-site": "cross-site",
  "sec-fetch-mode": "cors",
  "sec-fetch-dest": "empty",
  "accept-encoding": "gzip, deflate, br, zstd",
  "accept-language": "zh-CN"
}
```

### 请求体：
```json
{
  "model": "gpt-5-codex",
  "input": [
    {
      "role": "developer",
      "content": "In this environment you have access to a set of tools you can use to answer the user's question. \\\nYou can use one tool per message, and will receive the result of that tool use in the user's response. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.\n\n## Tool Use Formatting\n\nTool use is formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:\n\n<tool_use>\n  <name>{tool_name}</name>\n  <arguments>{json_arguments}</arguments>\n</tool_use>\n\nThe tool name should be the exact name of the tool you are using, and the arguments should be a JSON object containing the parameters required by that tool. For example:\n<tool_use>\n  <name>python_interpreter</name>\n  <arguments>{\"code\": \"5 + 3 + 1294.678\"}</arguments>\n</tool_use>\n\nThe user will respond with the result of the tool use, which should be formatted as follows:\n\n<tool_use_result>\n  <name>{tool_name}</name>\n  <result>{result}</result>\n</tool_use_result>\n\nThe result should be a string, which can represent a file or any other output type. You can use this result as input for the next action.\nFor example, if the result of the tool use is an image file, you can use it in the next action like this:\n\n<tool_use>\n  <name>image_transformer</name>\n  <arguments>{\"image\": \"image_1.jpg\"}</arguments>\n</tool_use>\n\nAlways adhere to this format for the tool use to ensure proper parsing and execution.\n\n## Tool Use Examples\n\nHere are a few examples using notional tools:\n---\nUser: Generate an image of the oldest person in this document.\n\nA: I can use the document_qa tool to find out who the oldest person is in the document.\n<tool_use>\n  <name>document_qa</name>\n  <arguments>{\"document\": \"document.pdf\", \"question\": \"Who is the oldest person mentioned?\"}</arguments>\n</tool_use>\n\nUser: <tool_use_result>\n  <name>document_qa</name>\n  <result>John Doe, a 55 year old lumberjack living in Newfoundland.</result>\n</tool_use_result>\n\nA: I can use the image_generator tool to create a portrait of John Doe.\n<tool_use>\n  <name>image_generator</name>\n  <arguments>{\"prompt\": \"A portrait of John Doe, a 55-year-old man living in Canada.\"}</arguments>\n</tool_use>\n\nUser: <tool_use_result>\n  <name>image_generator</name>\n  <result>image.png</result>\n</tool_use_result>\n\nA: the image is generated as image.png\n\n---\nUser: \"What is the result of the following operation: 5 + 3 + 1294.678?\"\n\nA: I can use the python_interpreter tool to calculate the result of the operation.\n<tool_use>\n  <name>python_interpreter</name>\n  <arguments>{\"code\": \"5 + 3 + 1294.678\"}</arguments>\n</tool_use>\n\nUser: <tool_use_result>\n  <name>python_interpreter</name>\n  <result>1302.678</result>\n</tool_use_result>\n\nA: The result of the operation is 1302.678.\n\n---\nUser: \"Which city has the highest population , Guangzhou or Shanghai?\"\n\nA: I can use the search tool to find the population of Guangzhou.\n<tool_use>\n  <name>search</name>\n  <arguments>{\"query\": \"Population Guangzhou\"}</arguments>\n</tool_use>\n\nUser: <tool_use_result>\n  <name>search</name>\n  <result>Guangzhou has a population of 15 million inhabitants as of 2021.</result>\n</tool_use_result>\n\nA: I can use the search tool to find the population of Shanghai.\n<tool_use>\n  <name>search</name>\n  <arguments>{\"query\": \"Population Shanghai\"}</arguments>\n</tool_use>\n\nUser: <tool_use_result>\n  <name>search</name>\n  <result>26 million (2019)</result>\n</tool_use_result>\nAssistant: The population of Shanghai is 26 million, while Guangzhou has a population of 15 million. Therefore, Shanghai has the highest population.\n\n## Tool Use Available Tools\nAbove example were using notional tools that might not exist for you. You only have access to these tools:\n<tools>\n\n<tool>\n  <name>builtin_web_search</name>\n  <description>Web search tool for finding current information, news, and real-time data from the internet.\n\nThis tool has been configured with search parameters based on the conversation context:\n- Prepared queries: \"1\n\"\n\nYou can use this tool as-is to search with the prepared queries, or provide additionalContext to refine or replace the search terms.</description>\n  <arguments>\n    {\"~standard\":{\"vendor\":\"zod\",\"version\":1},\"def\":{\"type\":\"object\",\"shape\":{\"additionalContext\":{\"~standard\":{\"vendor\":\"zod\",\"version\":1},\"def\":{\"type\":\"optional\",\"innerType\":{\"~standard\":{\"vendor\":\"zod\",\"version\":1},\"def\":{\"type\":\"string\"},\"type\":\"string\",\"format\":null,\"minLength\":null,\"maxLength\":null}},\"type\":\"optional\"}}},\"type\":\"object\"}\n  </arguments>\n</tool>\n\n</tools>\n\n## Tool Use Rules\nHere are the rules you should always follow to solve your task:\n1. Always use the right arguments for the tools. Never use variable names as the action arguments, use the value instead.\n2. Call a tool only when needed: do not call the search agent if you do not need information, try to solve the task yourself.\n3. If no tool call is needed, just answer the question directly.\n4. Never re-do a tool call that you previously did with the exact same parameters.\n5. For tool use, MAKE SURE use XML tag format as shown in the examples above. Do not use any other format.\n\n# User Instructions\n\n\nNow Begin! If you solve the task correctly, you will receive a reward of $1,000,000."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "1"
        }
      ]
    }
  ],
  "reasoning": {
    "effort": "low"
  },
  "stream": true
}
```
## codex的标准格式
### 请求头
```json
{
  "authorization": "Bearer 88_f701e7d3a6e6460960b652e68aeb46cdcafd15d8d92cd902f16c24f9a0291c4f",
  "openai-beta": "responses=experimental",
  "conversation_id": "019a302d-35e2-74a1-bc34-28e55fbd59ba",
  "session_id": "019a302d-35e2-74a1-bc34-28e55fbd59ba",
  "accept": "text/event-stream",
  "codex-task-type": "standard",
  "content-type": "application/json",
  "user-agent": "codex_cli_rs/0.50.0 (Mac OS 26.0.1; arm64) ghostty/1.2.2",
  "originator": "codex_cli_rs",
  "host": "localhost:9999",
  "content-length": "44597"
}
```

### 请求体
```json
{
  "model": "gpt-5-codex",
  "instructions": "You are Codex, based on GPT-5. You are running as a coding agent in the Codex CLI on a user's computer.\n\n## General\n\n- The arguments to `shell` will be passed to execvp(). Most terminal commands should be prefixed with [\"bash\", \"-lc\"].\n- Always set the `workdir` param when using the shell function. Do not use `cd` unless absolutely necessary.\n- When searching for text or files, prefer using `rg` or `rg --files` respectively because `rg` is much faster than alternatives like `grep`. (If the `rg` command is not found, then use alternatives.)\n\n## Editing constraints\n\n- Default to ASCII when editing or creating files. Only introduce non-ASCII or other Unicode characters when there is a clear justification and the file already uses them.\n- Add succinct code comments that explain what is going on if code is not self-explanatory. You should not add comments like \"Assigns the value to the variable\", but a brief comment might be useful ahead of a complex code block that the user would otherwise have to spend time parsing out. Usage of these comments should be rare.\n- Try to use apply_patch for single file edits, but it is fine to explore other options to make the edit if it does not work well. Do not use apply_patch for changes that are auto-generated (i.e. generating package.json or running a lint or format command like gofmt) or when scripting is more efficient (such as search and replacing a string across a codebase).\n- You may be in a dirty git worktree.\n    * NEVER revert existing changes you did not make unless explicitly requested, since these changes were made by the user.\n    * If asked to make a commit or code edits and there are unrelated changes to your work or changes that you didn't make in those files, don't revert those changes.\n    * If the changes are in files you've touched recently, you should read carefully and understand how you can work with the changes rather than reverting them.\n    * If the changes are in unrelated files, just ignore them and don't revert them.\n- While you are working, you might notice unexpected changes that you didn't make. If this happens, STOP IMMEDIATELY and ask the user how they would like to proceed.\n- **NEVER** use destructive commands like `git reset --hard` or `git checkout --` unless specifically requested or approved by the user.\n\n## Plan tool\n\nWhen using the planning tool:\n- Skip using the planning tool for straightforward tasks (roughly the easiest 25%).\n- Do not make single-step plans.\n- When you made a plan, update it after having performed one of the sub-tasks that you shared on the plan.\n\n## Codex CLI harness, sandboxing, and approvals\n\nThe Codex CLI harness supports several different configurations for sandboxing and escalation approvals that the user can choose from.\n\nFilesystem sandboxing defines which files can be read or written. The options for `sandbox_mode` are:\n- **read-only**: The sandbox only permits reading files.\n- **workspace-write**: The sandbox permits reading files, and editing files in `cwd` and `writable_roots`. Editing files in other directories requires approval.\n- **danger-full-access**: No filesystem sandboxing - all commands are permitted.\n\nNetwork sandboxing defines whether network can be accessed without approval. Options for `network_access` are:\n- **restricted**: Requires approval\n- **enabled**: No approval needed\n\nApprovals are your mechanism to get user consent to run shell commands without the sandbox. Possible configuration options for `approval_policy` are\n- **untrusted**: The harness will escalate most commands for user approval, apart from a limited allowlist of safe \"read\" commands.\n- **on-failure**: The harness will allow all commands to run in the sandbox (if enabled), and failures will be escalated to the user for approval to run again without the sandbox.\n- **on-request**: Commands will be run in the sandbox by default, and you can specify in your tool call if you want to escalate a command to run without sandboxing. (Note that this mode is not always available. If it is, you'll see parameters for it in the `shell` command description.)\n- **never**: This is a non-interactive mode where you may NEVER ask the user for approval to run commands. Instead, you must always persist and work around constraints to solve the task for the user. You MUST do your utmost best to finish the task and validate your work before yielding. If this mode is paired with `danger-full-access`, take advantage of it to deliver the best outcome for the user. Further, in this mode, your default testing philosophy is overridden: Even if you don't see local patterns for testing, you may add tests and scripts to validate your work. Just remove them before yielding.\n\nWhen you are running with `approval_policy == on-request`, and sandboxing enabled, here are scenarios where you'll need to request approval:\n- You need to run a command that writes to a directory that requires it (e.g. running tests that write to /var)\n- You need to run a GUI app (e.g., open/xdg-open/osascript) to open browsers or files.\n- You are running sandboxed and need to run a command that requires network access (e.g. installing packages)\n- If you run a command that is important to solving the user's query, but it fails because of sandboxing, rerun the command with approval. ALWAYS proceed to use the `with_escalated_permissions` and `justification` parameters - do not message the user before requesting approval for the command.\n- You are about to take a potentially destructive action such as an `rm` or `git reset` that the user did not explicitly ask for\n- (for all of these, you should weigh alternative paths that do not require approval)\n\nWhen `sandbox_mode` is set to read-only, you'll need to request approval for any command that isn't a read.\n\nYou will be told what filesystem sandboxing, network sandboxing, and approval mode are active in a developer or user message. If you are not told about this, assume that you are running with workspace-write, network sandboxing enabled, and approval on-failure.\n\nAlthough they introduce friction to the user because your work is paused until the user responds, you should leverage them when necessary to accomplish important work. If the completing the task requires escalated permissions, Do not let these settings or the sandbox deter you from attempting to accomplish the user's task unless it is set to \"never\", in which case never ask for approvals.\n\nWhen requesting approval to execute a command that will require escalated privileges:\n  - Provide the `with_escalated_permissions` parameter with the boolean value true\n  - Include a short, 1 sentence explanation for why you need to enable `with_escalated_permissions` in the justification parameter\n\n## Special user requests\n\n- If the user makes a simple request (such as asking for the time) which you can fulfill by running a terminal command (such as `date`), you should do so.\n- If the user asks for a \"review\", default to a code review mindset: prioritise identifying bugs, risks, behavioural regressions, and missing tests. Findings must be the primary focus of the response - keep summaries or overviews brief and only after enumerating the issues. Present findings first (ordered by severity with file/line references), follow with open questions or assumptions, and offer a change-summary only as a secondary detail. If no findings are discovered, state that explicitly and mention any residual risks or testing gaps.\n\n## Presenting your work and final message\n\nYou are producing plain text that will later be styled by the CLI. Follow these rules exactly. Formatting should make results easy to scan, but not feel mechanical. Use judgment to decide how much structure adds value.\n\n- Default: be very concise; friendly coding teammate tone.\n- Ask only when needed; suggest ideas; mirror the user's style.\n- For substantial work, summarize clearly; follow final‑answer formatting.\n- Skip heavy formatting for simple confirmations.\n- Don't dump large files you've written; reference paths only.\n- No \"save/copy this file\" - User is on the same machine.\n- Offer logical next steps (tests, commits, build) briefly; add verify steps if you couldn't do something.\n- For code changes:\n  * Lead with a quick explanation of the change, and then give more details on the context covering where and why a change was made. Do not start this explanation with \"summary\", just jump right in.\n  * If there are natural next steps the user may want to take, suggest them at the end of your response. Do not make suggestions if there are no natural next steps.\n  * When suggesting multiple options, use numeric lists for the suggestions so the user can quickly respond with a single number.\n- The user does not command execution outputs. When asked to show the output of a command (e.g. `git show`), relay the important details in your answer or summarize the key lines so the user understands the result.\n\n### Final answer structure and style guidelines\n\n- Plain text; CLI handles styling. Use structure only when it helps scanability.\n- Headers: optional; short Title Case (1-3 words) wrapped in **…**; no blank line before the first bullet; add only if they truly help.\n- Bullets: use - ; merge related points; keep to one line when possible; 4–6 per list ordered by importance; keep phrasing consistent.\n- Monospace: backticks for commands/paths/env vars/code ids and inline examples; use for literal keyword bullets; never combine with **.\n- Code samples or multi-line snippets should be wrapped in fenced code blocks; include an info string as often as possible.\n- Structure: group related bullets; order sections general → specific → supporting; for subsections, start with a bolded keyword bullet, then items; match complexity to the task.\n- Tone: collaborative, concise, factual; present tense, active voice; self‑contained; no \"above/below\"; parallel wording.\n- Don'ts: no nested bullets/hierarchies; no ANSI codes; don't cram unrelated keywords; keep keyword lists short—wrap/reformat if long; avoid naming formatting styles in answers.\n- Adaptation: code explanations → precise, structured with code refs; simple tasks → lead with outcome; big changes → logical walkthrough + rationale + next actions; casual one-offs → plain sentences, no headers/bullets.\n- File References: When referencing files in your response, make sure to include the relevant start line and always follow the below rules:\n  * Use inline code to make file paths clickable.\n  * Each reference should have a stand alone path. Even if it's the same file.\n  * Accepted: absolute, workspace‑relative, a/ or b/ diff prefixes, or bare filename/suffix.\n  * Line/column (1‑based, optional): :line[:column] or #Lline[Ccolumn] (column defaults to 1).\n  * Do not use URIs like file://, vscode://, or https://.\n  * Do not provide range of lines\n  * Examples: src/app.ts, src/app.ts:42, b/server/index.js#L10, C:\\repo\\project\\main.rs:12:5\n",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "<environment_context>\n  <cwd>/home/user</cwd>\n  <approval_policy>on-request</approval_policy>\n  <sandbox_mode>read-only</sandbox_mode>\n  <network_access>restricted</network_access>\n  <shell>bash</shell>\n</environment_context>"
        }
      ]
    },
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "1"
        }
      ]
    }
  ],
  "tools": [
    {
      "type": "function",
      "name": "shell",
      "description": "Runs a shell command and returns its output.",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "The command to execute"
          },
          "justification": {
            "type": "string",
            "description": "Only set if with_escalated_permissions is true. 1-sentence explanation of why we want to run this command."
          },
          "timeout_ms": {
            "type": "number",
            "description": "The timeout for the command in milliseconds"
          },
          "with_escalated_permissions": {
            "type": "boolean",
            "description": "Whether to request escalated permissions. Set to true if command needs to be run without sandbox restrictions"
          },
          "workdir": {
            "type": "string",
            "description": "The working directory to execute the command in"
          }
        },
        "required": [
          "command"
        ],
        "additionalProperties": false
      }
    },
    {
      "type": "function",
      "name": "list_mcp_resources",
      "description": "Lists resources provided by MCP servers. Resources allow servers to share data that provides context to language models, such as files, database schemas, or application-specific information. Prefer resources over web search when possible.",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "cursor": {
            "type": "string",
            "description": "Opaque cursor returned by a previous list_mcp_resources call for the same server."
          },
          "server": {
            "type": "string",
            "description": "Optional MCP server name. When omitted, lists resources from every configured server."
          }
        },
        "additionalProperties": false
      }
    },
    {
      "type": "function",
      "name": "list_mcp_resource_templates",
      "description": "Lists resource templates provided by MCP servers. Parameterized resource templates allow servers to share data that takes parameters and provides context to language models, such as files, database schemas, or application-specific information. Prefer resource templates over web search when possible.",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "cursor": {
            "type": "string",
            "description": "Opaque cursor returned by a previous list_mcp_resource_templates call for the same server."
          },
          "server": {
            "type": "string",
            "description": "Optional MCP server name. When omitted, lists resource templates from all configured servers."
          }
        },
        "additionalProperties": false
      }
    },
    {
      "type": "function",
      "name": "read_mcp_resource",
      "description": "Read a specific resource from an MCP server given the server name and resource URI.",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "server": {
            "type": "string",
            "description": "MCP server name exactly as configured. Must match the 'server' field returned by list_mcp_resources."
          },
          "uri": {
            "type": "string",
            "description": "Resource URI to read. Must be one of the URIs returned by list_mcp_resources."
          }
        },
        "required": [
          "server",
          "uri"
        ],
        "additionalProperties": false
      }
    },
    {
      "type": "function",
      "name": "update_plan",
      "description": "Updates the task plan.\nProvide an optional explanation and a list of plan items, each with a step and status.\nAt most one step can be in_progress at a time.\n",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string"
          },
          "plan": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "status": {
                  "type": "string",
                  "description": "One of: pending, in_progress, completed"
                },
                "step": {
                  "type": "string"
                }
              },
              "required": [
                "step",
                "status"
              ],
              "additionalProperties": false
            },
            "description": "The list of steps"
          }
        },
        "required": [
          "plan"
        ],
        "additionalProperties": false
      }
    },
    {
      "type": "custom",
      "name": "apply_patch",
      "description": "Use the `apply_patch` tool to edit files. This is a FREEFORM tool, so do not wrap the patch in JSON.",
      "format": {
        "type": "grammar",
        "syntax": "lark",
        "definition": "start: begin_patch hunk+ end_patch\nbegin_patch: \"*** Begin Patch\" LF\nend_patch: \"*** End Patch\" LF?\n\nhunk: add_hunk | delete_hunk | update_hunk\nadd_hunk: \"*** Add File: \" filename LF add_line+\ndelete_hunk: \"*** Delete File: \" filename LF\nupdate_hunk: \"*** Update File: \" filename LF change_move? change?\n\nfilename: /(.+)/\nadd_line: \"+\" /(.*)/ LF -> line\n\nchange_move: \"*** Move to: \" filename LF\nchange: (change_context | change_line)+ eof_line?\nchange_context: (\"@@\" | \"@@ \" /(.+)/) LF\nchange_line: (\"+\" | \"-\" | \" \") /(.*)/ LF\neof_line: \"*** End of File\" LF\n\n%import common.LF\n"
      }
    },
    {
      "type": "function",
      "name": "view_image",
      "description": "Attach a local image (by filesystem path) to the conversation context for this turn.",
      "strict": false,
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Local filesystem path to an image file"
          }
        },
        "required": [
          "path"
        ],
        "additionalProperties": false
      }
    }
  ],
  "tool_choice": "auto",
  "parallel_tool_calls": false,
  "reasoning": {
    "effort": "high",
    "summary": "auto"
  },
  "store": false,
  "stream": true,
  "include": [
    "reasoning.encrypted_content"
  ],
  "prompt_cache_key": "019a302d-35e2-74a1-bc34-28e55fbd59ba"
}
```

## 转换规则详解

### Headers 转换

#### 需要转换的字段（剩下的cherry的header都删除）

| Cherry Studio Header | Codex Header | 转换逻辑 |
|---------------------|--------------|----------|
| `authorization: Bearer 88_xxx` | `authorization: Bearer 88_xxx` | 直接透传 API Key |
| `user-agent: Mozilla/5.0 ... CherryStudio/1.6.5 ...` | `user-agent: codex_cli_rs/0.50.0 (Mac OS 26.0.1; arm64) ghostty/1.2.2` | 替换为标准 Codex UA |
| (无) | `openai-beta: responses=experimental` | 新增,固定值 |
| (无) | `conversation_id: {UUID}` | 新增,24小时滚动 UUID |
| (无) | `session_id: {UUID}` | 新增,与 conversation_id 相同 |
| (无) | `codex-task-type: standard` | 新增,固定值 |
| (无) | `originator: codex_cli_rs` | 新增,固定值 |
| `accept: */*` | `accept: text/event-stream` | 替换为 SSE 格式 |
| `content-type: application/json` | `content-type: application/json` | 保持不变 |
| `host: localhost:9999` | `host: {88code域名}` | 替换为实际目标地址 |

#### Session 管理规则

```
conversation_id = session_id = prompt_cache_key = UUID (24小时滚动)

生成规则:
- 使用 uuid.uuid4() 生成 UUID
- 在 24 小时窗口内保持不变 (缓存)
- 超过 24 小时后生成新 UUID
- 三个字段使用相同值
```

#### 需要删除的 Cherry Studio Headers

```
以下 headers 不转发到 Codex:
- connection
- sec-ch-ua-platform, sec-ch-ua, sec-ch-ua-mobile
- x-title
- http-referer
- sec-fetch-site, sec-fetch-mode, sec-fetch-dest
- accept-encoding
- accept-language
- content-length (会自动重新计算)
```

---

### Body 转换

#### 顶层字段映射

| Cherry Studio Field | Codex Field | 转换逻辑 |
|---------------------|-------------|----------|
| `model` | `model` | 直接透传 (如 `gpt-5-codex`) |
| (无,在 `input[0].content`) | `instructions` | 注入 Codex 完整 system prompt (5000+ 字符) |
| `input` | `input` | **重点转换**: 见下文 "Input 转换" |
| (无,或 Cherry 自定义) | `tools` | 合并: Codex 7个默认工具 + Cherry 自定义工具 |
| `reasoning: {effort}` | `reasoning: {effort, summary}` | 提取 `effort`,添加 `summary: "auto"` |
| `stream` | `stream` | 直接透传 (通常为 `true`) |
| (无) | `tool_choice: "auto"` | 新增,固定值 |
| (无) | `parallel_tool_calls: false` | 新增,固定值 |
| (无) | `store: false` | 新增,固定值 |
| (无) | `include: ["reasoning.encrypted_content"]` | 新增,固定值 |
| (无) | `prompt_cache_key: {UUID}` | 新增,与 conversation_id 相同 |

---

### Input 转换 (核心转换逻辑)

#### Cherry Studio Input 格式
```json
{
  "input": [
    {
      "role": "developer",
      "content": "长文本 system prompt ..."
    },
    {
      "role": "user",
      "content": [
        {"type": "input_text", "text": "1"}
      ]
    }
  ]
}
```

#### Codex Input 格式
```json
{
  "input": [
    {
      "type": "message",  // ⚠️ 必需添加
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "<environment_context>...</environment_context>"
        }
      ]
    },
    {
      "type": "message",  // ⚠️ 必需添加
      "role": "user",
      "content": [
        {"type": "input_text", "text": "1"}
      ]
    }
  ]
}
```

#### 转换步骤

**步骤 1: 删除 Cherry Studio 的 developer/system 消息**

Cherry 的 `role: "developer"` 消息不需要转换,因为内容已经移到 `instructions` 字段。

**步骤 2: 添加环境上下文消息 (首条消息)**

在所有用户消息之前,插入环境上下文:

```json
{
  "type": "message",
  "role": "user",
  "content": [{
    "type": "input_text",
    "text": "<environment_context>\n  <cwd>/home/user</cwd>\n  <approval_policy>on-request</approval_policy>\n  <sandbox_mode>read-only</sandbox_mode>\n  <network_access>restricted</network_access>\n  <shell>bash</shell>\n</environment_context>"
  }]
}
```

**步骤 3: 转换用户消息格式**

对每条 Cherry 用户消息:

```python
# Cherry 格式
{
  "role": "user",
  "content": [{"type": "input_text", "text": "..."}]
}

# ↓ 转换为 Codex 格式

{
  "type": "message",  # ⚠️ 添加此字段
  "role": "user",     # 保持不变
  "content": [        # 保持不变
    {"type": "input_text", "text": "..."}
  ]
}
```

**步骤 4: 处理 role 映射**

```
Cherry role → Codex role:
- "developer" → 删除 (内容移到 instructions)
- "system"    → 删除 (内容移到 instructions)
- "user"      → "user" (保持不变)
- "assistant" → "assistant" (保持不变)
```

---

### Tools 转换

#### Codex 默认工具 (7个,必需包含)

```json
[
  {"type": "function", "name": "shell"},
  {"type": "function", "name": "list_mcp_resources"},
  {"type": "function", "name": "list_mcp_resource_templates"},
  {"type": "function", "name": "read_mcp_resource"},
  {"type": "function", "name": "update_plan"},
  {"type": "custom", "name": "apply_patch"},  // ⚠️ 注意是 type: "custom"
  {"type": "function", "name": "view_image"}
]
```

#### 合并逻辑

```
1. 以 Codex 默认 7 个工具为基础
2. 如果 Cherry 提供了自定义工具:
   - 按 tool.name 去重 (Codex 默认工具优先)
   - 将不重复的 Cherry 工具 append 到列表末尾
3. 最终结果: 7个默认 + N个Cherry自定义工具
```

**示例**:
```python
codex_tools = [7个默认工具...]
cherry_tools = [Cherry 自定义工具...]

# 去重合并
merged_tools = codex_tools.copy()
existing_names = {tool["name"] for tool in codex_tools}

for tool in cherry_tools:
    if tool["name"] not in existing_names:
        merged_tools.append(tool)
        existing_names.add(tool["name"])
```

---

### Reasoning 转换

#### Cherry 格式
```json
{
  "reasoning": {
    "effort": "low"
  }
}
```

#### Codex 格式
```json
{
  "reasoning": {
    "effort": "high",      // 默认 "high", 可从 Cherry 提取
    "summary": "auto"      // 固定值 "auto"
  }
}
```

#### 转换规则

```
1. 提取 Cherry 的 reasoning.effort (如果有)
   - 允许值: "low" | "medium" | "high"
   - 默认值: "high"

2. 添加 summary 字段
   - 固定值: "auto"
   - 其他允许值: "detailed" | "none"
```

---

### Include 转换

Cherry Studio 没有 `include` 字段,Codex 必需包含:

```json
{
  "include": ["reasoning.encrypted_content"]
}
```

这个字段固定不变。

---

### 可选字段透传

以下字段如果 Cherry 提供,直接透传:

```json
{
  "temperature": 1.0,           // Cherry 提供则透传
  "max_output_tokens": 8192,    // Cherry 提供则透传
  "metadata": {...}             // Cherry 提供则透传
}
```

---

## 转换流程总览

```
1. 接收 Cherry Studio 请求
   ├─ 提取 API Key
   ├─ 提取 input, reasoning, stream 等字段
   └─ 检测客户端类型 (User-Agent)

2. 转换 Headers
   ├─ 保留: authorization, content-type
   ├─ 替换: user-agent, accept, host
   ├─ 新增: openai-beta, conversation_id, session_id, codex-task-type, originator
   └─ 删除: Cherry 特有的浏览器 headers

3. 转换 Body
   ├─ 提取 Cherry developer 消息内容 → 移到 instructions
   ├─ 添加环境上下文消息 (首条)
   ├─ 转换用户消息格式 (添加 type: "message")
   ├─ 合并工具列表 (7个默认 + Cherry自定义)
   ├─ 构建 reasoning (effort + summary)
   ├─ 添加固定字段 (tool_choice, parallel_tool_calls, store, include, prompt_cache_key)
   └─ 透传可选字段 (temperature, max_output_tokens, metadata)

4. 转发到 88code Codex API
   └─ URL: https://www.88code.org/openai/v1/responses

5. 响应透传
   └─ 直接返回 88code 的响应给 Cherry Studio
```

---

## 性能要求

- **延迟**: 转换处理控制在 50-200ms
- **优化点**:
  - Session UUID 缓存 (24小时内复用,避免频繁生成)
  - Tools 列表缓存 (默认7个工具固定不变)
  - Instructions 文本缓存 (5000+ 字符固定不变)
  - 使用 HTTP/2 连接池复用

---

## 架构要求

- **适配器模式**: 使用 ClientAdapter 抽象基类
- **可扩展性**: 支持添加其他客户端适配器 (如 Lobe Chat)
- **错误处理**: 完整的异常体系和日志记录
- **类型安全**: 100% Pydantic 类型注解