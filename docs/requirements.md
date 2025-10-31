# 需求规格说明

> CC-Proxy 项目技术需求和实现规格

## 📋 项目概述

### 项目目标
实现 CherryStudio 客户端的 v1/response 请求到标准 OpenAI v1/response 请求的转换代理服务，要求架构合理，性能损耗在 50-200ms。

### 核心功能
- **双服务架构**: Claude API 代理 + OpenAI Codex API 代理
- **智能适配**: 自动检测客户端类型并转换请求格式
- **低延迟**: 请求转换性能损耗 ≤ 200ms
- **高可用**: 支持并发请求和故障恢复

---

## 🔄 数据转换规格

### CherryStudio → OpenAI 转换

#### 请求头转换
```diff
- openai-beta: responses=experimental
+ openai-beta: responses=experimental  # 保持不变
- user-agent: Mozilla/5.0 ... CherryStudio/1.6.5 ...
+ user-agent: codex_cli_rs/0.50.0 (标准 Codex UA)
```

#### 请求体转换

**输入格式 (CherryStudio)**:
```json
{
  "model": "gpt-5-codex",
  "input": [
    {"role": "system", "content": "system prompt"},
    {"role": "user", "content": "user input"}
  ],
  "tools": [...],
  "reasoning": {"effort": "high"},
  "max_output_tokens": 8192,
  "stream": false
}
```

**输出格式 (OpenAI)**:
```json
{
  "model": "gpt-5-codex",
  "input": [
    {"role": "system", "content": "system prompt + instructions"},
    {"role": "user", "content": "user input"}
  ],
  "tools": [default_tools + user_tools],
  "reasoning": {"effort": "high"},
  "max_output_tokens": 8192,
  "stream": true,  // 强��启用流式
  "metadata": {
    "user_id": "session_id",
    "approval_policy": "on-request",
    "conversation_id": "generated_id"
  }
}
```

---

## 📊 详细转换规则

### 1. 系统提示词处理

**策略**: 在现有 system prompt 基础上注入 Codex instructions

```python
def transform_system_prompt(original_system, instructions):
    if not original_system:
        return instructions
    return f"{instructions}\n\n{original_system}"
```

**注入内容**:
```text
You are Codex, based on GPT-5, a large language model trained to help with computer programming and software engineering tasks.

You are connected to a user through the Codex interface, which allows you to help users with their software engineering tasks.

You should follow these rules:
- 你的回答将作为直接的代码建议或解决方案呈现
- 始终遵循用户的���令和偏好
- 提供准确、高效、安全的代码建议
- 如果不确定，请要求澄清而不是做出假设
[... 其他 instructions ...]
```

### 2. 工具集合合并

**默认工具 (7个)**:
- `shell` - 执行 shell 命令
- `apply_patch` - 应用代码补丁
- `list_mcp_resources` - 列出 MCP 资源
- `read_mcp_resource` - 读取 MCP 资源
- `write_mcp_resource` - 写入 MCP 资源
- `edit_mcp_resource` - 编辑 MCP 资源
- `call_mcp_tool` - 调用 MCP 工具

**合并策略**: `default_tools + client_tools`

### 3. 字段映射表

| 字段 | 输入 (CherryStudio) | 输出 (OpenAI) | 处理方式 |
|------|---------------------|---------------|----------|
| `model` | `gpt-5-codex` | `gpt-5-codex` | 透传 |
| `input` | 消息数组 | 消息数组 | 合并 system prompt |
| `tools` | 客户端工具 | 工具集合 | 合并默认工具 |
| `reasoning` | 对象 | 对象 | 透传 |
| `max_output_tokens` | 数字 | 数字 | 透传 |
| `stream` | false | true | 强制为 true |
| `metadata` | 无 | 对象 | 新增 |
| `user_id` | 无 | session_id | 新增 |
| `approval_policy` | 无 | "on-request" | 新增 |
| `conversation_id` | 无 | generated_id | 新增 |

### 4. Session 管理

**Session ID 格式**: `user_proxy_account__session_{date}-{half_day}-{counter}`

**轮换机制**: 每12小时轮换一次，最大化API缓存命中率

```python
# 示例 Session ID
user_proxy_account__session_2025-10-31-0-1  # 00:00-12:00
user_proxy_account__session_2025-10-31-1-1  # 12:00-24:00
```

---

## 🏗️ 架构需求

### 性能要求

| 指标 | 要求 | 说明 |
|------|------|------|
| 响应延迟 | ≤ 200ms | 转换处理时间 |
| 并发处理 | 100+ QPS | 同时处理请求数 |
| 内存占用 | ≤ 200MB | 单服务实例 |
| 可用性 | 99.9% | 服务可用性 |

### 技术栈要求

- **后端框架**: FastAPI 0.115+
- **Python版本**: 3.11+
- **类型检查**: Pydantic 2.10+ (100%类型注解)
- **HTTP客户端**: httpx (HTTP/2支持)
- **日志系统**: structlog (结构化日志)
- **容器化**: Docker + Docker Compose

### 安全要求

- **API密钥**: 支持透传或统一配置
- **输入验证**: Pydantic模型验证所有输入
- **错误处理**: 不泄露内部错误信息
- **日志安全**: 生产环境不记录敏感数据

---

## 🔧 接口规格

### API 端点

#### service-cc (Claude代理)
```
POST http://localhost:8001/v1/messages
GET  http://localhost:8001/health
GET  http://localhost:8001/adapters
```

#### service-cx (Codex代理)
```
POST http://localhost:8002/v1/responses
GET  http://localhost:8002/health
GET  http://localhost:8002/adapters
```

### 健康检查响应
```json
{
  "status": "healthy",
  "service": "service-cx",
  "version": "1.0.0",
  "timestamp": "2025-10-31T12:00:00Z"
}
```

### 错误响应格式
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid request format",
    "details": {...}
  }
}
```

---

## 📦 部署需求

### 环境配置

#### 开发环境
```bash
ENVIRONMENT=test
LOG_LEVEL=DEBUG
ANTHROPIC_BASE_URL=https://api.anthropic.com
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### 生产环境
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
ANTHROPIC_BASE_URL=https://api.anthropic.com
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Docker要求
- **���础镜像**: python:3.11-slim
- **内存限制**: 512MB
- **CPU限制**: 1核
- **健康检查**: 30秒间隔
- **重启策略**: unless-stopped

---

## 🧪 测试需求

### 单元测试
- 适配器检测逻辑
- 数据转换函数
- Session生成逻辑
- 错误处理机制

### 集成测试
- 端到端API测试
- 并发请求测试
- 错误恢复测试
- 性能基准测试

### 测试工具
```bash
# 运行验证脚本
python scripts/validate_adapter.py

# 测试API端点
curl http://localhost:8001/health
curl http://localhost:8002/health
```

---

## 📝 变更管理

### 版本控制
- **主版本**: 架构重大变更
- **次版本**: 新功能添加
- **修订版本**: Bug修复和优化

### 文档要求
- **架构文档**: 同步更新设计变更
- **API文档**: 保持接口描述准确
- **部署文档**: 更新配置和部署流程
- **变更日志**: 记录所有重要变更

---

**需求版本**: v1.0.0
**最后更新**: 2025-10-31
**状态**: 已实现