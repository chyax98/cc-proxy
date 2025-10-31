# CC-Proxy - FastAPI 双服务代理

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

生产级 FastAPI 双服务架构,提供 Claude 和 Codex API 的智能代理和格式转换服务。

## ✨ 核心特性

- 🏗️ **双服务架构** - Claude Service + Codex Service (已移除 Gateway 层)
- 🔄 **智能适配器** - 自动检测客户端类型并转换请求格式
- 🚀 **高性能** - HTTP/2 + 异步 I/O + 连接池优化
- 📡 **流式响应** - SSE 实时流式传输,零缓冲转发
- 🎯 **类型安全** - 100% Pydantic 类型注解
- 🐳 **统一启动** - start.py 根据环境自动选择 uvicorn/gunicorn
- 📝 **环境日志** - 生产环境不打日志,测试环境记录详细请求/响应

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│              客户端 (CherryStudio, Lobe, etc.)       │
└──────────────┬──────────────────┬───────────────────┘
               │                  │
    ┌──────────▼────────┐  ┌─────▼──────────────┐
    │ Claude Service    │  │ Codex Service      │
    │     :8001         │  │     :8002          │
    │ ────────────────  │  │ ─────────────────  │
    │ • 适配器系统      │  │ • 适配器系统       │
    │ • 格式转换        │  │ • 格式转换         │
    │ • Session 管理    │  │ • API 代理         │
    │ • API 代理        │  │                    │
    └──────────┬────────┘  └─────┬──────────────┘
               │                  │
      ┌────────▼────────┐  ┌─────▼─────────┐
      │ Anthropic API   │  │  OpenAI API   │
      │ (88code)        │  │ (88code)      │
      └─────────────────┘  └───────────────┘
```

**架构说明**:
- 两个独立服务直接暴露端点,无 Gateway 中间层
- 客户端直接访问 service-cc:8001 或 service-cx:8002
- 符合 KISS 原则,减少不必要的网络跳转

详细架构设计请查看: [CLAUDE.md](CLAUDE.md)

## 📦 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/yourusername/cc-proxy.git
cd cc-proxy

# 安装 uv (如未安装)
pip install uv

# 安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env

# 编辑配置
vim .env
```

### 2. 启动服务

#### 🚀 统一启动脚本 (推荐)

```bash
# 开发环境 (uvicorn + reload)
ENVIRONMENT=test python start.py

# 生产环境 (gunicorn + 4 workers)
ENVIRONMENT=production python start.py
```

#### 🔧 手动启动 (开发调试)

```bash
# Claude Service
uv run uvicorn service-cc.main:app --host 0.0.0.0 --port 8001 --reload

# Codex Service (另一个终端)
uv run uvicorn service-cx.main:app --host 0.0.0.0 --port 8002 --reload
```

### 3. 验证服务

```bash
# Claude Service 健康检查
curl http://localhost:8001/health
# {"status": "healthy", "service": "claude-service"}

# Codex Service 健康检查
curl http://localhost:8002/health
# {"status": "healthy", "service": "codex-service"}
```

## 🎯 核心功能

### Claude 服务 (Port 8001)

**端点**:
- `POST /v1/messages` - 创建消息
- `GET /adapters` - 列出适配器
- `GET /health` - 健康检查

**适配器**:
- **CherryStudioAdapter**: 检测 CherryStudio UA 或 `thinking` 字段
  - 注入 Claude Code system prompt
  - 保留 `thinking` 字段并透传给 88code
  - 添加 12 小时轮换 session

**使用示例**:

```bash
curl -X POST http://localhost:8001/v1/messages \
  -H "x-api-key: sk-ant-xxx" \
  -H "User-Agent: CherryStudio/1.0.0" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "thinking": {"enabled": true},
    "stream": true
  }'
```

### Codex 服务 (Port 8002)

**端点**:
- `POST /v1/responses` - 创建响应 (OpenAI Responses API)
- `GET /v1` - API 信息
- `GET /health` - 健康检查

**适配器**:
- **CustomAdapter**: 检测 `x-client-type` header
- **DefaultAdapter**: 默认透传

**使用示例**:

```bash
curl -X POST http://localhost:8002/v1/responses \
  -H "Authorization: Bearer sk-xxx" \
  -d '{
    "model": "gpt-4o",
    "input": "Implement a web server in Rust"
  }'
```

## ⚙️ 配置

### 环境变量 (.env)

```bash
# 环境配置
ENVIRONMENT=production          # production (生产) | test (测试)

# Claude Service 配置
CLAUDE_SERVICE_HOST=0.0.0.0
CLAUDE_SERVICE_PORT=8001

# Codex Service 配置
CODEX_SERVICE_HOST=0.0.0.0
CODEX_SERVICE_PORT=8002

# 外部 API
ANTHROPIC_BASE_URL=https://www.88code.org/api
OPENAI_BASE_URL=https://www.88code.org/openai/v1

# 日志配置
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                 # json, console

# HTTP 客户端
HTTP_TIMEOUT=120.0
HTTP_CONNECT_TIMEOUT=10.0
HTTP_MAX_KEEPALIVE=100
HTTP_MAX_CONNECTIONS=200
HTTP_KEEPALIVE_EXPIRY=30.0
```

### 环境说明

**Production (生产环境)**:
- 使用 gunicorn + 4 workers
- 不记录详细请求/响应体日志
- 适合生产部署

**Test (测试环境)**:
- 使用 uvicorn + reload
- 记录详细请求/响应体日志
- 适合开发调试

## 📝 日志策略

### 生产环境 (ENVIRONMENT=production)
```json
{
  "event": "claude_request",
  "model": "claude-sonnet-4",
  "stream": false,
  "message_count": 3,
  "user_agent": "CherryStudio/1.0.0"
}
```
**说明**: 只记录元数据,不记录请求体/响应体

### 测试环境 (ENVIRONMENT=test)
```json
{
  "event": "claude_request",
  "model": "claude-sonnet-4",
  "stream": false,
  "message_count": 3,
  "user_agent": "CherryStudio/1.0.0",
  "request_body": {
    "model": "claude-sonnet-4",
    "messages": [...]
  }
}
```
**说明**: 记录完整的请求体和响应体,用于调试

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 编程语言 |
| **FastAPI** | 0.115+ | Web 框架 |
| **Pydantic** | 2.10+ | 数据验证 |
| **httpx** | 0.28+ | HTTP 客户端 (HTTP/2) |
| **Uvicorn** | 0.34+ | ASGI 服务器 (开发) |
| **Gunicorn** | 23.0+ | WSGI 服务器 (生产) |
| **structlog** | 24.4+ | 结构化日志 |
| **uv** | 最新 | 包管理 |
| **Pytest** | 8.3+ | 测试框架 |

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **延迟 (P50)** | <30ms | 服务处理延迟 |
| **延迟 (P95)** | <100ms | 95% 请求延迟 |
| **吞吐量** | >800 QPS | 单实例吞吐 |
| **内存** | <150MB | 单服务内存占用 |
| **并发** | 1000+ | HTTP/2 并发连接 |

### 优化措施

- ✅ HTTP/2 连接池 (复用 TCP 连接)
- ✅ 异步 I/O (asyncio + httpx)
- ✅ 连接池管理 (100 keepalive, 200 max)
- ✅ 流式响应 (零缓冲转发)
- ✅ 环境日志 (生产环境减少日志开销)
- ✅ Gunicorn 多进程 (生产环境 4 workers)

## 📖 文档

- **[CLAUDE.md](CLAUDE.md)** - AI 开发指南和完整架构文档
- **[claudedocs/](claudedocs/)** - 专家评审报告和优化建议

## 🔒 安全特性

- ✅ API Key 验证 (x-api-key, Authorization header)
- ✅ 敏感信息脱敏 (生产环境不记录请求体)
- ✅ 结构化日志 (JSON 格式)
- ✅ CORS 跨域策略

## 📞 常见问题

### 端口冲突

修改 `.env` 中的端口配置:

```bash
CLAUDE_SERVICE_PORT=8001
CODEX_SERVICE_PORT=8002
```

### 依赖安装失败

确保 uv 已安装:

```bash
pip install uv
uv sync
```

### 如何切换环境?

```bash
# 测试环境 (详细日志)
ENVIRONMENT=test python start.py

# 生产环境 (精简日志)
ENVIRONMENT=production python start.py
```

### API Key 错误

检查 header 格式:

- Claude: `x-api-key: sk-ant-xxx`
- Codex: `Authorization: Bearer sk-xxx`

## 🚧 架构演进

### v1.0.0 (当前版本)
- ✅ 移除 Gateway 层,简化架构
- ✅ 统一启动脚本 (start.py)
- ✅ 环境日志策略 (production/test)
- ✅ Gunicorn 生产部署

### 后续规划
- [ ] Docker / Kubernetes 部署配置
- [ ] 更多适配器 (Lobe-Chat, OpenCat)
- [ ] 监控面板 (Grafana)
- [ ] 性能优化 (异步日志)
- [ ] Redis 缓存集成

## 📝 许可证

MIT © 2025

## 🙏 致谢

本项目基于 KISS/DRY/YAGNI 原则开发,由 Claude Code 协助完成。

---

**项目状态**: ✅ 生产就绪

**版本**: 1.0.0

**最后更新**: 2025-10-30
