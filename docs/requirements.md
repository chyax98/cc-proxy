# 需求规格

## 📋 项目目标

实现 CherryStudio 到 OpenAI v1/response 的转换代理，性能损耗 ≤ 200ms。

## 🔄 数据转换

### 输入 (CherryStudio)
```json
{
  "model": "gpt-5-codex",
  "input": [{"role": "user", "content": "..."}],
  "tools": [...],
  "stream": false
}
```

### 输出 (OpenAI)
```json
{
  "model": "gpt-5-codex",
  "input": [{"role": "system", "content": "instructions + ..."}, {"role": "user", "..."}],
  "tools": [default_tools + client_tools],
  "stream": true,
  "metadata": {"user_id": "session_id"}
}
```

## 📊 关键处理

1. **系统提示词**: 注入 Codex instructions
2. **工具合并**: 默认7个工具 + 客户端工具
3. **流式响应**: 强制 `stream=true`
4. **Session管理**: 12小时轮换

## 🏗️ 技术要求

- **框架**: FastAPI 0.115+, Python 3.11+
- **性能**: 延迟 ≤ 200ms, 并发 100+ QPS
- **内存**: ≤ 200MB
- **安全**: API密钥透传，输入验证

## 🔧 API端点

- **service-cc**: `:8001/v1/messages`
- **service-cx**: `:8002/v1/responses`
- **健康检查**: `/health`

---

**v1.0.0** | **2025-10-31**