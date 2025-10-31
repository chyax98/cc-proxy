# CC-Proxy 文档中心

> 项目核心文档索引

## 📋 核心文档

### 🚀 快速开始
- **[README.md](../README.md)** - 项目介绍和快速开始指南

### 🏗️ 架构文档
- **[CLAUDE.md](CLAUDE.md)** - AI 开发指南（主文档）

### 🚀 部署运维
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker 部署指南

### 🔧 开发调试
- **[DEBUG.md](DEBUG.md)** - 调试指南和故障排除

---

## 📖 推荐阅读顺序

### 新开发者
1. [README.md](../README.md) - 了解项目概况
2. [CLAUDE.md](CLAUDE.md) - 深入架构设计
3. [DEPLOYMENT.md](DEPLOYMENT.md) - 学习部署方法

### 架构师
1. [CLAUDE.md](CLAUDE.md) - 核心架构文档
2. [README.md](../README.md) - 了解项目功能

### 运维工程师
1. [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
2. [README.md](../README.md) - 了解服务架构

---

## 🚀 快速命令

### 启动服务
```bash
# 开发环境 (uvicorn + reload)
ENVIRONMENT=test python start.py

# 生产环境 (gunicorn + 4 workers)
ENVIRONMENT=production python start.py
```

### 健康检查
```bash
curl http://localhost:8001/health  # service-cc
curl http://localhost:8002/health  # service-cx
```

### 测试端点
```bash
# Claude API
curl -X POST http://localhost:8001/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_API_KEY" \
  -H "User-Agent: CherryStudio/1.0" \
  -d '{"model":"claude-sonnet-4","messages":[...]}'

# Codex API
curl -X POST http://localhost:8002/v1/responses \
  -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  -H "User-Agent: CherryStudio/1.0" \
  -d '{"model":"gpt-5-codex","input":"test"}'
```

---

## 📂 项目结构

```
.
├── CLAUDE.md                    # 项目技术文档 (AI 开发指南)
├── README.md                    # 用户使用指南
├── start.py                     # 统一启动脚本
├── common/                      # 共享库
│   ├── adapters/                # 统一适配器基类
│   ├── config.py                # 配置管理
│   ├── logger.py                # 结构化日志
│   ├── http_client.py           # HTTP/2 客户端
│   └── errors.py                # 异常体系
├── service-cc/                  # Claude 代理服务 :8001
│   ├── adapters/                # 客户端适配器
│   ├── formats/                 # 格式定义 (system prompt, session)
│   ├── schemas/                 # Pydantic 数据模型
│   ├── main.py                  # FastAPI 应用
│   ├── router.py                # API 路由
│   └── proxy.py                 # Anthropic API 代理
├── service-cx/                  # Codex 代理服务 :8002
│   ├── adapters/                # 客户端适配器
│   ├── formats/                 # 格式定义 (instructions, tools, session)
│   ├── schemas/                 # Pydantic 数据模型
│   ├── main.py                  # FastAPI 应用
│   ├── router.py                # API 路由
│   ├── proxy.py                 # OpenAI API 代理
│   ├── request_logger.py        # 链路追踪日志
│   └── debug_logger.py          # 调试输出
└── claudedocs/                  # 技术文档
    ├── ARCHITECTURE-CONSISTENCY.md  # 架构一致性和转换策略 ⭐⭐⭐⭐⭐
    └── README.md                    # 文档索引 (本文件)
```

```

---

## 📚 文档维护

### 更新原则
- **准确性**: 确保文档与实际代码一致
- **及时性**: 重大变更后 24 小时内更新文档
- **可读性**: 使用清晰的标记和示例

### 文档版本
- **主文档** (CLAUDE.md): v2.3.0 (2025-10-31)
- **其他文档**: 随项目版本更新

### 贡献指南
- 新增功能请同步更新相关文档
- 发现文档错误请提交 Issue 或 PR
- 文档变更应包含在相关 Commit 中

---

## 🔗 相关资源

- **FastAPI 文档**: https://fastapi.tiangolo.com
- **Anthropic API**: https://docs.anthropic.com
- **OpenAI API**: https://platform.openai.com/docs
- **Pydantic 文档**: https://docs.pydantic.dev

---

**最后更新**: 2025-10-31
**维护者**: AI Development Team
