# 启动调试模式

## 快速启动

```bash
# 确保在测试环境
export ENVIRONMENT=test

# 启动服务
uv run python -m service-cx.main
```

## 调试输出说明

启动后,当有请求进来时,你会看到清晰的输出:

### 1. 请求摘要
```
================================================================================
📤 发送到目标API的请求
================================================================================

【基本信息】
  模型: gpt-5-codex
  流式: True
  工具选择: auto
  ...

【Reasoning 配置】
  推理深度: high
  摘要模式: auto

【Instructions】
  长度: 5135 字符
  前 100 字符: You are Codex, based on GPT-5...

【Input 消息】共 2 条
  1. type=message, role=user, content_blocks=1
     预览: <environment_context>...
  2. type=message, role=user, content_blocks=1
     预览: 你的实际问题...

【Tools 工具】共 44 个  ← 重点看这里!应该是 44,不是 7
  默认工具 (7): shell, apply_patch, list_mcp_resources, ...
  MCP 工具 (37):
    - chrome-devtools: 26 个工具
      • click
      • navigate_page
      • take_screenshot
      ... 还有 23 个
    - context7: 2 个工具
    - searxng: 2 个工具
    - ...

【请求体大小】
  JSON 大小: 47,234 bytes (46.1 KB)  ← 应该接近 47745
  预期 Content-Length: 47234
```

### 2. 响应摘要
```
================================================================================
📥 目标API响应
================================================================================

  HTTP 状态码: 200  ← 成功!
  Content-Type: text/event-stream
  ✅ 请求成功!
```

或者如果出错:
```
  HTTP 状态码: 400
  Content-Type: text/event-stream
  ❌ 400 Bad Request - 请求格式错误
  错误详情: (错误信息)
```

## 验证检查点

1. **工具数量**: 应该显示 `共 7 个` (默认工具,客户端工具会自动 append)
2. **流式模式**: 应该显示 `流式: True` ⚠️ **stream 必须为 true**
3. **HTTP 状态**: 应该是 200,而不是 400

## ✅ 已修复: stream 字段问题

**问题**: 某些兼容服务的 Responses API 在 `stream=false` 时可能有 bug,返回 400 错误:

```json
{
  "error": {
    "message": "Cannot invoke \"ErrorEvent.getType()\" because \"error\" is null"
  }
}
```

**解决方案**: 已在 `service-cx/adapters/cherry_studio.py:78` 强制设置:

```python
"stream": True,  # 强制 stream=true,某些兼容服务不支持 stream=false
```

**验证**: 使用真实抓包的完整请求测试成功:
- ✅ 44 个工具 (7 默认 + 37 MCP)
- ✅ 10939 字符 instructions
- ✅ HTTP 200 + SSE 流式响应

详细调试过程: `/claudedocs/stream-field-fix.md`

## 如果还是 400 错误

检查以下内容:

1. **API Key 是否正确**
   ```bash
   echo $OPENAI_API_KEY | head -c 20  # 只显示前20个字符确认格式
   ```

2. **stream 字段是否为 true**
   - 查看日志中 `流式: True`
   - 如果是 False,说明强制设置没生效

3. **请求体大小是否正确**
   - 查看日志中 `JSON 大小: X bytes`
   - 至少应该有 15KB+ (instructions + tools)

## 手动测试 (可选)

如果服务还是 400,可以尝试手动 curl 测试:

```bash
# 保存一个最简单的请求
cat > test_minimal.json <<EOF
{
  "model": "gpt-4",
  "input": [{"role": "user", "content": "test"}]
}
EOF

# 测试目标API是否支持 Responses API
curl -X POST $OPENAI_BASE_URL/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "openai-beta: responses=experimental" \
  -d @test_minimal.json -v
```

如果这个也返回 400,说明问题不在我们的代码,而是目标API的配置或兼容性问题。
