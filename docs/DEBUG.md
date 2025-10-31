# 调试指南

> 开发调试和故障排除手册

## 🚀 快速启动调试

### 启动调试模式

```bash
# 确保在测试环境
export ENVIRONMENT=test

# 启动服务（详细日志）
python start.py
```

### 调试输出说明

启动后，当有请求进来时，会看到清晰��结构化日志输出：

### 1. 请求摘要
```
================================================================================
📤 发送到目标API的请求
================================================================================

【基本信息】
  模型: gpt-4o
  流式: True
  工具选择: auto

【Instructions】
  长度: 5135 字符
  前 100 字符: You are Codex, based on GPT-5...

【Input 消息】共 2 条
  1. type=message, role=user, content_blocks=1
     预览: <environment_context>...
  2. type=message, role=user, content_blocks=1
     预览: 用户问题...

【Tools 工具】共 7 个
  默认工具: shell, apply_patch, list_mcp_resources, ...

【请求体大小】
  JSON 大小: 47,234 bytes (46.1 KB)
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

## 🔧 常见问题排查

### 1. API Key 问题

**症状**: 401 Unauthorized 错误

**检查方法**:
```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY | head -c 20  # 只显示前20个字符确认格式
echo $OPENAI_API_KEY | head -c 20

# 检查配置文件
cat .env | grep API_KEY
```

**解决方案**:
- 确保 API Key 格式正确
- 检查 API Key 是否有效
- 确认环境变量已正确设置

### 2. 连接问题

**症状**: 连接超时或网络错误

**检查方法**:
```bash
# 测试网络连接
curl -I $ANTHROPIC_BASE_URL
curl -I $OPENAI_BASE_URL

# 检查代理设置
echo $http_proxy
echo $https_proxy
```

**解决方案**:
- 检查网络连接
- 配置代理（如需要）
- 验证 API 端点可访问性

### 3. 流式响应问题

**症状**: 400 Bad Request 错误

**问题描述**: 某些兼容服务的 Responses API 在 `stream=false` 时有 bug

**解决方案**: 已在代码中强制设置 `stream=true`

```python
# service-cx/adapters/cherry_studio.py
"stream": True,  # 强制 stream=true
```

**验证检查��**:
1. **工具数量**: 应该显示 `共 7 个` (默认工具)
2. **流式模式**: 应该显示 `流式: True`
3. **HTTP 状态**: 应该是 200,而不是 400

### 4. 适配器问题

**症状**: 请求未被正确转换

**检查方法**:
```bash
# 查看适配器列表
curl http://localhost:8001/adapters
curl http://localhost:8002/adapters

# 查看详细日志
ENVIRONMENT=test python start.py
```

**解决方案**:
- 检查 User-Agent 是否正确
- 验证适配器是否已注册
- 确认请求格式符合预期

## 🔍 高级调试技巧

### 1. 启用详细日志

```bash
# 设置调试级别
export LOG_LEVEL=DEBUG
export ENVIRONMENT=test

# 启动服务
python start.py
```

### 2. 单独测试服务

```bash
# 只启动 Claude 服务
python -m service-cc.main

# 只启动 Codex 服务
python -m service-cx.main
```

### 3. 手动测试 API

```bash
# 测试 Claude API
cat > claude_test.json <<EOF
{
  "model": "claude-sonnet-4",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 100
}
EOF

curl -X POST http://localhost:8001/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d @claude_test.json -v

# 测试 Codex API
cat > codex_test.json <<EOF
{
  "model": "gpt-4o",
  "input": [{"role": "user", "content": "test"}]
}
EOF

curl -X POST http://localhost:8002/v1/responses \
  -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @codex_test.json -v
```

### 4. 检查服务状态

```bash
# 健康检查
curl http://localhost:8001/health
curl http://localhost:8002/health

# 服务信息
curl http://localhost:8001/v1
curl http://localhost:8002/v1
```

## 🐛 Docker 环境调试

### 1. 查看容器日志

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f cc-proxy
```

### 2. 进入容器调试

```bash
# 进入容器
docker-compose exec cc-proxy bash

# 查看服务状态
ps aux | grep python
curl localhost:8001/health
curl localhost:8002/health
```

### 3. 容器网络调试

```bash
# 查看网络配置
docker-compose exec cc-proxy env | grep BASE_URL

# 测试外部连接
docker-compose exec cc-proxy curl -I $ANTHROPIC_BASE_URL
```

## 📊 性能调试

### 1. 监控资源使用

```bash
# 查看内存使用
docker stats cc-proxy

# 查看进程状态
ps aux | grep python
```

### 2. 压力测试

```bash
# 安装压力测试工具
pip install httpx

# 简单并发测试
python -c "
import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get('http://localhost:8001/health')
            for _ in range(100)
        ]
        responses = await asyncio.gather(*tasks)
        print(f'成功: {sum(1 for r in responses if r.status_code == 200)}/100')

asyncio.run(test())
"
```

## 📝 调试检查清单

### 启动前检查
- [ ] 环境变量已正确设置
- [ ] API Key 有效且权限正确
- [ ] 网络连接正常
- [ ] 端口未被占用

### 运行时检查
- [ ] 服务健康检查通过
- [ ] 适配器正确加载
- [ ] 日志输出正常
- [ ] API 响应格式正确

### 问题排查
- [ ] 查看详细错误日志
- [ ] 检查网络连接
- [ ] 验证 API Key
- [ ] 测试手动请求

---

**更新时间**: 2025-10-31
**维护者**: CC-Proxy Development Team