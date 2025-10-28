# Claude Code Proxy

> 🎭 伪装成 Claude Code CLI 的智能代理服务，让 CherryStudio 等第三方客户端享受 Claude Code 优惠策略

## 🚀 核心特性

- **🎯 自动检测 CherryStudio 请求** - 智能识别并增强第三方客户端
- **🔄 System 身份注入** - 注入 Claude Code 官方身份声明
- **💾 12小时会话缓存** - 自动轮换 session，最大化 API 缓存利用率
- **⚡ HTTP 连接池** - Keep-Alive 连接复用，降低延迟
- **🛡️ 稳定性保障** - 流式响应错误处理、断线清理
- **📦 零文件 I/O** - 模板内联到代码，避免启动开销

## 📊 性能优化

| 优化项 | 改进 |
|--------|------|
| **JSON 模板加载** | 内联到代码（避免文件 I/O） |
| **HTTP 连接** | 连接池复用（减少 ~50ms TCP 握手） |
| **调试日志** | 移除文件写入（消除 5-20ms 阻塞） |
| **Session 管理** | 12小时缓存（提升 cache_control 效率） |

## 🔧 快速开始

### 安装依赖

```bash
npm install
```

### 配置环境变量

创建 `.env` 文件：

```env
# 可选：统一 API Key（留空则使用客户端传递的 Key）
ANTHROPIC_API_KEY=

# 上游 API 地址
ANTHROPIC_BASE_URL=https://www.88code.org/api

# 监听端口
PORT=3001
```

### 启动服务

```bash
# 开发模式
node server.js

# 生产模式（后台运行）
nohup node server.js > logs/production.log 2>&1 &
```

### 验证服务

```bash
# 健康检查
curl http://localhost:3001/health

# 查看服务信息
curl http://localhost:3001/
```

## 🎮 客户端配置

### CherryStudio

1. 打开设置 → 服务提供商
2. 添加自定义 Anthropic 端点：
   ```
   http://localhost:3001
   ```
3. 填入你的 88code API Key
4. 开始使用！

## 📡 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/messages` | POST | 对话生成（支持流式） |
| `/v1/messages/count_tokens` | POST | Token 计数 |
| `/health` | GET | 健康检查 |
| `/` | GET | 服务信息 |

## 🎭 工作原理

```
CherryStudio → Proxy (检测+增强) → 88code API
                ↓
         1. 检测 Cherry UA
         2. 注入 Claude Code system
         3. 添加 12h session
         4. 伪装请求头
```

## 📝 技术细节

### System 注入内容

```json
[
  {
    "type": "text",
    "text": "You are Claude Code, Anthropic's official CLI for Claude.",
    "cache_control": {
      "type": "ephemeral"
    }
  }
]
```

**仅 121 字符**，相比原版 12KB+ 的完整注入降低了 **99%**！

### Session ID 格式

```
user_88code_proxy_account__session_88code-cherry-2025-10-29-40779
                                           ↑日期    ↑12小时计数器
```

- 每 12 小时自动轮换
- 同一时段内所有请求共享 session
- 充分利用 API 的 `cache_control: ephemeral`

### 伪装请求头

```javascript
{
  'user-agent': 'claude-cli/2.0.24 (external, cli)',
  'anthropic-beta': 'claude-code-20250219',
  'x-app': 'cli',
  'x-stainless-runtime': 'node',
  // ... 完整 Claude Code 特征
}
```

## 🔐 安全说明

- ✅ 所有 API Key 仅转发，不存储
- ✅ 支持环境变量统一 Key（可选）
- ✅ 支持客户端自带 Key（灵活）
- ✅ CORS 开启（支持网页客户端）

## 📦 项目结构

```
anthropic-proxy/
├── server.js              # 主服务（HTTP 代理 + 连接池）
├── enhancer.js            # Cherry 请求增强逻辑
├── package.json           # 依赖配置
├── .env                   # 环境变量（需自行创建）
├── .gitignore             # Git 忽略规则
└── logs/                  # 日志目录
```

## 🛠️ 故障排查

### 服务无法启动

```bash
# 检查端口占用
lsof -i :3001

# 查看日志
tail -f logs/production.log
```

### Cherry 请求未被识别

确保：
1. User-Agent 包含 `CherryStudio`
2. 或请求中无 `tools` 字段
3. 或 `system` 不包含 "You are Claude Code"

### API 响应错误

```bash
# 测试上游 API
curl -X POST https://www.88code.org/api/v1/messages \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"model":"claude-sonnet-4-5-20250929","messages":[{"role":"user","content":"test"}]}'
```

## 📄 License

MIT

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [88code.org](https://www.88code.org/) - Claude 中转服务
- [CherryStudio](https://github.com/kangfenmao/cherry-studio) - 优秀的 AI 客户端

---

**⚠️ 免责声明**：本项目仅供学习交流，请遵守 Anthropic 服务条款。
