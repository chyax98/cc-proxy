import express from 'express';
import fetch from 'node-fetch';
import http from 'http';
import https from 'https';
import dotenv from 'dotenv';
import { PluginManager } from './plugins/manager.js';
import { ClaudeCodePlugin } from './plugins/claude-code.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const ANTHROPIC_BASE_URL = process.env.ANTHROPIC_BASE_URL || 'https://www.88code.org/api';

// HTTP连接池配置
const httpAgent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 100,
  maxFreeSockets: 10
});

const httpsAgent = new https.Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 100,
  maxFreeSockets: 10
});

// 初始化插件管理器
const pluginManager = new PluginManager();

// 注册默认插件
pluginManager.register(new ClaudeCodePlugin());

// 中间件：解析 JSON
app.use(express.json({ limit: '50mb' }));

// CORS 中间件
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-api-key, anthropic-api-key, anthropic-version, anthropic-beta');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Credentials', 'true');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  next();
});

/**
 * 提取API Key（支持多种格式）
 */
function extractApiKey(req) {
  if (ANTHROPIC_API_KEY) {
    return ANTHROPIC_API_KEY;
  }

  if (req.headers.authorization) {
    const auth = req.headers.authorization;
    if (auth.startsWith('Bearer ') || auth.startsWith('bearer ')) {
      return auth.substring(7);
    }
    return auth;
  }

  if (req.headers['x-api-key']) {
    return req.headers['x-api-key'];
  }

  if (req.headers['anthropic-api-key']) {
    return req.headers['anthropic-api-key'];
  }

  return null;
}

// 代理 /v1/messages 端点
app.post('/v1/messages', async (req, res) => {
  try {
    // 提取API Key
    const apiKey = extractApiKey(req);
    if (!apiKey) {
      return res.status(401).json({
        type: 'error',
        error: {
          type: 'authentication_error',
          message: 'Missing API key'
        }
      });
    }

    // 使用插件系统处理请求
    const result = pluginManager.process(req.body, req.headers);

    let headers;
    if (result) {
      // 匹配到插件，使用插件转换
      req.body = result.body;
      headers = result.getHeaders(apiKey);
      console.log(`🎭 Plugin: ${result.plugin.name} v${result.plugin.version}`);
    } else {
      // 无匹配插件，直接透传
      headers = {
        'authorization': `Bearer ${apiKey}`,
        'content-type': 'application/json'
      };
    }

    // 转发请求到上游API
    const anthropicUrl = `${ANTHROPIC_BASE_URL}/v1/messages`;
    const response = await fetch(anthropicUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(req.body),
      agent: ANTHROPIC_BASE_URL.startsWith('https') ? httpsAgent : httpAgent
    });

    // 处理流式响应
    if (req.body.stream) {
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      response.body.on('error', (err) => {
        console.error('Stream error:', err.message);
        if (!res.headersSent) {
          res.status(500).end();
        }
      });

      req.on('close', () => {
        response.body.destroy();
      });

      response.body.pipe(res);
    }
    // 处理非流式响应
    else {
      const data = await response.json();
      res.status(response.status).json(data);
    }

  } catch (error) {
    console.error('Proxy error:', error.message);

    if (!res.headersSent) {
      res.status(500).json({
        type: 'error',
        error: {
          type: 'api_error',
          message: error.message
        }
      });
    }
  }
});

// Token 计数端点
app.post('/v1/messages/count_tokens', async (req, res) => {
  try {
    const apiKey = extractApiKey(req);
    if (!apiKey) {
      return res.status(401).json({
        type: 'error',
        error: {
          type: 'authentication_error',
          message: 'Missing API key'
        }
      });
    }

    const headers = {
      'authorization': `Bearer ${apiKey}`,
      'content-type': 'application/json'
    };

    const response = await fetch(`${ANTHROPIC_BASE_URL}/v1/messages/count_tokens`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(req.body),
      agent: ANTHROPIC_BASE_URL.startsWith('https') ? httpsAgent : httpAgent
    });

    const data = await response.json();
    res.status(response.status).json(data);

  } catch (error) {
    console.error('Token count error:', error.message);

    if (!res.headersSent) {
      res.status(500).json({
        type: 'error',
        error: {
          type: 'api_error',
          message: error.message
        }
      });
    }
  }
});

// 插件管理端点
app.get('/plugins', (req, res) => {
  res.json({
    plugins: pluginManager.list(),
    total: pluginManager.plugins.size
  });
});

// 健康检查
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'anthropic-proxy',
    timestamp: new Date().toISOString(),
    api_key_configured: !!ANTHROPIC_API_KEY,
    target: ANTHROPIC_BASE_URL,
    plugins: pluginManager.plugins.size
  });
});

// 根路径
app.get('/', (req, res) => {
  res.json({
    name: 'Anthropic Proxy (Plugin-based Architecture)',
    version: '2.0.0',
    description: '基于插件架构的协议转换代理服务',
    endpoints: {
      messages: 'POST /v1/messages',
      count_tokens: 'POST /v1/messages/count_tokens',
      plugins: 'GET /plugins',
      health: 'GET /health'
    },
    features: {
      plugin_system: 'Extensible protocol conversion plugins',
      connection_pool: 'HTTP keep-alive for performance',
      stream_support: 'Server-Sent Events streaming',
      auto_detection: 'Automatic client detection'
    }
  });
});

// 启动服务器
app.listen(PORT, '0.0.0.0', () => {
  console.log('🚀 Anthropic Proxy Started (Plugin-based)');
  console.log(`📍 Listening: http://0.0.0.0:${PORT}`);
  console.log(`🔗 Target: ${ANTHROPIC_BASE_URL}`);
  console.log(`🔑 API Key: ${ANTHROPIC_API_KEY ? 'Configured' : 'From clients'}`);
  console.log(`🔌 Plugins: ${pluginManager.plugins.size} loaded`);
  pluginManager.list().forEach(p => {
    console.log(`   - ${p.name} v${p.version}: ${p.description}`);
  });
});

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('Shutting down gracefully...');
  pluginManager.destroyAll();
  process.exit(0);
});
