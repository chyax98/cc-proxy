# 调试指南

## 🚀 启动调试

```bash
ENVIRONMENT=test python start.py
```

## 🔧 常见问题

### API Key 错误 (401)
```bash
echo $ANTHROPIC_API_KEY | head -c 20
echo $OPENAI_API_KEY | head -c 20
```

### 连接问题
```bash
curl -I $ANTHROPIC_BASE_URL
curl -I $OPENAI_BASE_URL
```

### 400错误检查
- 检查 `stream=true`
- 验证工具数量 (7个)
- 确认HTTP状态为200

## 🐛 Docker调试

```bash
docker-compose logs -f
docker-compose exec cc-proxy bash
```

## 📝 测试命令

```bash
# 健康检查
curl http://localhost:8001/health
curl http://localhost:8002/health

# 查看适配器
curl http://localhost:8001/adapters
curl http://localhost:8002/adapters
```

---

**v1.0.0** | **2025-10-31**