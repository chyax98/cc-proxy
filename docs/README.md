# CC-Proxy 文档中心

> 项目核心文档索引

## 📋 核心文档

### 🚀 快速开始
- **[README.md](../README.md)** - 项目介绍和快速开始指南

### 🏗️ 架构文档
- **[CLAUDE.md](CLAUDE.md)** - 核心架构文档（必读）

### 🚀 部署运维
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker 部署指南

### 🔧 开发调试
- **[DEBUG.md](DEBUG.md)** - 调试指南和故障排除

### 📋 需求规格
- **[requirements.md](requirements.md)** - 详细技术需求

---

## 📖 推荐阅读顺序

### 新开发者
1. [README.md](../README.md) - 了解项目概况
2. [CLAUDE.md](CLAUDE.md) - 深入架构设计
3. [DEPLOYMENT.md](DEPLOYMENT.md) - 学习部署方法

### 架构师
1. [CLAUDE.md](CLAUDE.md) - 核心架构文档
2. [requirements.md](requirements.md) - 技术需求规格

### 运维工程师
1. [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
2. [DEBUG.md](DEBUG.md) - 故障排除

### 开发者
1. [CLAUDE.md](CLAUDE.md) - 架构和开发规范
2. [DEBUG.md](DEBUG.md) - 调试技巧

---

## 🚀 快速命令

### 启动服务
```bash
# 开发环境 (uvicorn + reload)
ENVIRONMENT=test python start.py

# 生产环境 (gunicorn + 多进程)
ENVIRONMENT=production python start.py
```

### 健康检查
```bash
curl http://localhost:8001/health  # Claude Service
curl http://localhost:8002/health  # Codex Service
```

### 测试端点
```bash
# Claude API
curl -X POST http://localhost:8001/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4","messages":[{"role":"user","content":"test"}]}'

# Codex API
curl -X POST http://localhost:8002/v1/responses \
  -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","input":"test"}'
```

---

## 📚 文档维护

### 更新原则
- **准确性**: 确保文档与实际代码一致
- **及时性**: 重大变更后 24 小时内更新文档
- **可读性**: 使用清晰的标记和示例

### 文档版本
- **主文档**: v1.0.0 (2025-10-31)
- **更新频率**: 随项目版本同步更新

### 贡献指南
- 新增功能请同步更新相关文档
- 发现文档错误请提交 Issue 或 PR
- 文档变更应包含在相关 Commit 中

---

## 🔗 相关资源

- **项目仓库**: https://github.com/chyax98/cc-proxy
- **FastAPI 文档**: https://fastapi.tiangolo.com
- **Docker 文档**: https://docs.docker.com
- **Pydantic 文档**: https://docs.pydantic.dev

---

**最后更新**: 2025-10-31
**维护者**: CC-Proxy Development Team