# 部署指南

## ✅ 已完成部署

### 服务状态

```bash
# 查看 PM2 状态
pm2 status

# 查看日志
pm2 logs anthropic-proxy

# 重启服务
pm2 restart anthropic-proxy

# 停止服务
pm2 stop anthropic-proxy
```

### 本地测试

```bash
# 健康检查
curl http://127.0.0.1:3001/health

# 查看服务信息
curl http://127.0.0.1:3001/

# 测试消息API（需要真实 API Key）
curl -X POST http://127.0.0.1:3001/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-ant-xxxxx" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🌐 外网访问配置（宝塔面板）

### 步骤 1：添加 DNS 记录

在你的 DNS 提供商（如 Cloudflare）添加：

```
类型: A
名称: api
值: 117.72.152.220
TTL: Auto
```

验证 DNS 生效：

```bash
nslookup api.chyax.site
```

### 步骤 2：宝塔面板配置站点

1. **添加站点**
   - 登录宝塔面板: https://chyax.site:8888
   - 网站 → 添加站点
   - 域名: `api.chyax.site`
   - 根目录: `/www/wwwroot/api.chyax.site`（随意，不使用）
   - PHP 版本: 纯静态
   - 数据库: 不创建

2. **配置反向代理**
   - 点击站点设置 → 反向代理 → 添加反向代理
   - 配置名称: `anthropic-proxy`
   - 代理名称: `anthropic-proxy`
   - 目标 URL: `http://127.0.0.1:3001`
   - 发送域名: `$host`
   - 内容替换: （留空）

3. **高级配置**（可选，点击配置文件）

   在 `location /` 块中添加：

   ```nginx
   location / {
       proxy_pass http://127.0.0.1:3001;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;

       # 支持 SSE 流式响应
       proxy_http_version 1.1;
       proxy_set_header Connection "";
       proxy_buffering off;
       chunked_transfer_encoding off;

       # 超时设置
       proxy_connect_timeout 60s;
       proxy_send_timeout 90s;
       proxy_read_timeout 90s;
   }
   ```

4. **申请 SSL 证书**
   - 站点设置 → SSL → Let's Encrypt
   - 勾选 `api.chyax.site`
   - 点击申请
   - 开启强制 HTTPS

### 步骤 3：测试外网访问

```bash
# HTTP 测试（如果没开启强制 HTTPS）
curl http://api.chyax.site/health

# HTTPS 测试
curl https://api.chyax.site/health

# 预期响应
{
  "status": "healthy",
  "service": "anthropic-proxy",
  "timestamp": "2025-10-29T12:00:00.000Z",
  "api_key_configured": false,
  "target": "https://api.anthropic.com"
}
```

## 📱 客户端配置

### Cherry Studio

```
API 类型: Anthropic
API 地址: https://api.chyax.site/v1
API Key: sk-ant-xxxxx（你的真实 Anthropic Key）
模型: claude-3-5-sonnet-20241022
```

### Cursor / 其他 IDE

```bash
export ANTHROPIC_BASE_URL=https://api.chyax.site
export ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### cURL 测试

```bash
curl -X POST https://api.chyax.site/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-ant-xxxxx" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "测试消息"}]
  }'
```

## 📊 日志查看

### PM2 日志

```bash
# 实时查看所有日志
pm2 logs anthropic-proxy

# 只看错误日志
pm2 logs anthropic-proxy --err

# 只看输出日志
pm2 logs anthropic-proxy --out

# 清空日志
pm2 flush
```

### 日志文件位置

```
/root/app/claude-code-proxy/anthropic-proxy/logs/
├── error.log    # 错误日志
└── output.log   # 输出日志
```

查看日志文件：

```bash
tail -f /root/app/claude-code-proxy/anthropic-proxy/logs/output.log
```

## 🔧 故障排查

### 问题 1：PM2 服务未运行

```bash
pm2 status
pm2 restart anthropic-proxy
```

### 问题 2：端口被占用

```bash
# 查看 3001 端口占用
lsof -i :3001

# 或者修改端口
nano .env
# 修改 PORT=3002
pm2 restart anthropic-proxy
```

### 问题 3：Nginx 502 错误

```bash
# 检查服务是否运行
curl http://127.0.0.1:3001/health

# 检查 Nginx 配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 问题 4：SSL 证书问题

- 确保 DNS 已生效（等待 5-10 分钟）
- 重新申请证书
- 检查 80 端口是否开放

## 🔒 安全建议

1. **API Key 管理**

   在 `.env` 中配置统一的 Key，避免客户端直接传递：

   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

2. **IP 白名单（可选）**

   在 Nginx 配置中添加：

   ```nginx
   location / {
       allow 你的IP;
       deny all;
       proxy_pass http://127.0.0.1:3001;
   }
   ```

3. **速率限制（可选）**

   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

   location / {
       limit_req zone=api_limit burst=20 nodelay;
       proxy_pass http://127.0.0.1:3001;
   }
   ```

## 📈 监控

### PM2 Monit

```bash
pm2 monit
```

### 系统资源

```bash
# CPU 和内存占用
pm2 status

# 详细信息
pm2 show anthropic-proxy
```

## 🔄 更新代码

```bash
cd /root/app/claude-code-proxy/anthropic-proxy
git pull  # 如果使用 Git
pm2 restart anthropic-proxy
```

## ⚠️ 重要提示

1. **请求头版本**：
   - `claude-cli/1.0.25` 可能会过时
   - 定期查看 [GitHub Issues](https://github.com/anthropics/claude-code/issues) 获取最新版本

2. **Beta 标识**：
   - `claude-code-20250219` 是日期标识
   - 如果 API 返回错误，可能需要更新此值

3. **日志监控**：
   - 代理会记录所有请求的客户端 User-Agent
   - 定期查看日志了解使用情况

## 📞 支持

如遇问题：
1. 查看 PM2 日志: `pm2 logs anthropic-proxy`
2. 查看 Nginx 错误日志: `tail -f /www/server/nginx/logs/api.chyax.site.error.log`
3. 检查防火墙: `firewall-cmd --list-ports`
