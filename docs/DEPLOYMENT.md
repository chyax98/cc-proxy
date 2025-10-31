# CC-Proxy 快速部署指南

## 📋 部署概览

CC-Proxy 支持 3 种部署方式：
1. **本地开发** - 直接运行 Python 脚本
2. **Docker 容器** - 单容器部署
3. **Docker Compose** - 生产环境推荐

---

## 🚀 方式一：本地开发部署

### 前置要求
- Python 3.11+
- uv (推荐的 Python 包管理器)

### 快速启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd cc_cx-proxy

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API Keys 等

# 4. 启动开发环境
ENVIRONMENT=test python start.py

# 5. 验证服务
curl http://localhost:8001/health  # Claude Service
curl http://localhost:8002/health  # Codex Service
```

### 生产环境启动

```bash
# 生产环境启动 (自动优化内存和 worker 数量)
ENVIRONMENT=production python start.py
```

---

## 🐳 方式二：Docker 单容器部署

### 构建镜像

```bash
# 构建镜像
docker build -t cc-proxy:latest .

# 或者使用 buildx (多平台支持)
docker buildx build -t cc-proxy:latest --platform linux/amd64,linux/arm64 .
```

### 运行容器

```bash
# 开发环境 (挂载代码，支持热重载)
docker run -d \
  --name cc-proxy-dev \
  -p 8001:8001 -p 8002:8002 \
  -v $(pwd):/app \
  -e ENVIRONMENT=test \
  -e CONTAINER_MODE=true \
  cc-proxy:latest

# 生产环境
docker run -d \
  --name cc-proxy \
  -p 8001:8001 -p 8002:8002 \
  -e ENVIRONMENT=production \
  -e CONTAINER_MODE=true \
  --memory=512m \
  --cpus=1.0 \
  --restart unless-stopped \
  cc-proxy:latest
```

---

## 🏭 方式三：Docker Compose 部署 (推荐)

### 生产环境部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 验证服务
curl http://localhost:8001/health
curl http://localhost:8002/health

# 5. 查看资源使用
docker stats cc-proxy-app
```

### 开发环境部署

```bash
# 开发环境 (支持代码热重载)
docker-compose -f docker-compose.dev.yml up -d

# 查看实时日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 服务管理

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d --force-recreate

# 清理
docker-compose down -v  # 删除卷
docker system prune -f  # 清理未使用的镜像
```

---

## ⚙️ 环境变量配置

### 必需配置

```bash
# 基础配置
ENVIRONMENT=production              # production | test
LOG_LEVEL=INFO                      # DEBUG | INFO | WARNING | ERROR

# 服务端口
CLAUDE_SERVICE_HOST=0.0.0.0
CLAUDE_SERVICE_PORT=8001
CODEX_SERVICE_HOST=0.0.0.0
CODEX_SERVICE_PORT=8002

# 外部 API
ANTHROPIC_BASE_URL=https://www.88code.org/api
OPENAI_BASE_URL=https://www.88code.org/openai
```

### 可选配置

```bash
# 调试配置 (仅开发环境)
CODEX_DUMP_REQUESTS=false          # 是否保存请求到文件
CODEX_DUMP_DIR=/tmp/dumps           # 请求保存目录

# 容器优化
CONTAINER_MODE=true                 # 启用容器模式优化
DEBUG=false                         # 是否显示详细错误信息
```

---

## 📊 资源限制和优化

### Docker Compose 配置

```yaml
# 生产环境限制 (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 512M      # 最大内存 512MB
      cpus: '1.0'       # 最大 CPU 1 核
    reservations:
      memory: 256M      # 预留内存 256MB
      cpus: '0.5'       # 预留 CPU 0.5 核
```

### 内存优化特性

- **智能 Worker 调整**: 根据可用内存自动调整 worker 数量
- **垃圾回收优化**: 容器模式��更频繁的垃圾回收
- **请求限制**: 自动重启 worker 防止内存泄漏
- **连接限制**: 减少连接数降低内存占用

### 性能调优

```bash
# 监控内存使用
docker stats cc-proxy-app

# 查看容器内存详情
docker exec cc-proxy-app cat /proc/meminfo

# 调整内存限制 (编辑 docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 1G        # 增加到 1GB
```

---

## 🔍 健康检查和监控

### 健康检查端点

```bash
# Claude Service 健康检查
curl http://localhost:8001/health
# 返回: {"status": "healthy", "service": "claude-service", "version": "1.0.0"}

# Codex Service 健康检查
curl http://localhost:8002/health
# 返回: {"status": "healthy", "service": "codex-service", "version": "1.0.0"}

# API 信息
curl http://localhost:8001/v1
curl http://localhost:8002/v1
```

### 日志查看

```bash
# Docker Compose 日志
docker-compose logs -f

# 单独服务日志
docker-compose logs -f cc-proxy

# 容器内日志
docker exec cc-proxy-app tail -f /app/logs/*.log
```

---

## 🚨 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :8001
   lsof -i :8002

   # 修改端口 (编辑 .env)
   CLAUDE_SERVICE_PORT=8011
   CODEX_SERVICE_PORT=8012
   ```

2. **内存不足**
   ```bash
   # 增加内存限制
   docker-compose down
   # 编辑 docker-compose.yml，增加 memory 限制
   docker-compose up -d
   ```

3. **启动失败**
   ```bash
   # 查看详细日志
   docker-compose logs cc-proxy

   # 启用调试模式
   docker-compose down
   # 编辑 docker-compose.yml，添加:
   # - DEBUG=true
   docker-compose up -d
   ```

### 性能问题排查

```bash
# 查看容器资源使用
docker stats cc-proxy-app

# 查看容器内进程
docker exec cc-proxy-app ps aux

# 查看内存详细情况
docker exec cc-proxy-app free -h
```

---

## 📈 扩展和高可用

### 多实例部署

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  cc-proxy:
    build: .
    scale: 3  # 3 个实例
    # ... 其他配置
```

```bash
# 启动多实例
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### 负载均衡

使用 Nginx 或 HAProxy 进行负载均衡：

```nginx
# nginx.conf 示例
upstream cc_proxy {
    server localhost:8001;
    server localhost:8003;  # 第二个实例
    server localhost:8004;  # 第三个实例
}

server {
    listen 80;
    location / {
        proxy_pass http://cc_proxy;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔐 安全建议

1. **使用非 root 用户**: Dockerfile 已配置
2. **限制网络访问**: 使用 Docker 网络
3. **定期更新**: 及时更新镜像和依赖
4. **监控日志**: 设置日志监控和告警
5. **备份配置**: 定期备份 .env 和配置文件

---

## 📞 支持

- **文档**: [CLAUDE.md](./CLAUDE.md) - 详细架构文档
- **配置示例**: [.env.example](./.env.example)
- **问题报告**: 提交 Issue 到项目仓库

---

**部署完成后，访问 http://localhost:8001/health 和 http://localhost:8002/health 验证服务是否正常运行！** 🎉