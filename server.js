import express from 'express';
import fetch from 'node-fetch';
import http from 'http';
import https from 'https';
import dotenv from 'dotenv';
import { enhanceCherryRequest } from './enhancer.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const ANTHROPIC_BASE_URL = process.env.ANTHROPIC_BASE_URL || 'https://www.88code.org/api';

// HTTP连接池配置（复用TCP连接，提升性能）
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

// Claude Code CLI 的请求头特征（基于官方 2.0.24 版本）
const CLAUDE_CODE_HEADERS = {
  'accept': 'application/json',
  'anthropic-beta': 'claude-code-20250219',
  'anthropic-dangerous-direct-browser-access': 'true',
  'anthropic-version': '2023-06-01',
  'content-type': 'application/json',
  'user-agent': 'claude-cli/2.0.24 (external, cli)',
  'x-app': 'cli',
  'x-stainless-arch': 'x64',
  'x-stainless-lang': 'js',
  'x-stainless-os': 'Linux',
  'x-stainless-runtime': 'node',
  'x-stainless-runtime-version': 'v22.16.0'
};

/**
 * 提取API Key（支持多种格式）
 */
function extractApiKey(req) {
  // 1. 环境变量优先
  if (ANTHROPIC_API_KEY) {
    return ANTHROPIC_API_KEY;
  }

  // 2. Authorization头（Bearer格式）
  if (req.headers.authorization) {
    const auth = req.headers.authorization;
    if (auth.startsWith('Bearer ') || auth.startsWith('bearer ')) {
      return auth.substring(7);
    }
    return auth;
  }

  // 3. x-api-key头
  if (req.headers['x-api-key']) {
    return req.headers['x-api-key'];
  }

  // 4. anthropic-api-key头
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

    // 增强Cherry请求（伪装成Claude Code）
    req.body = enhanceCherryRequest(req.body, req.headers);

    // 构建伪装请求头
    const headers = {
      ...CLAUDE_CODE_HEADERS,
      'authorization': `Bearer ${apiKey}`
    };

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

      // 错误处理
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
      ...CLAUDE_CODE_HEADERS,
      'authorization': `Bearer ${apiKey}`
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

// 健康检查
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'anthropic-proxy',
    timestamp: new Date().toISOString(),
    api_key_configured: !!ANTHROPIC_API_KEY,
    target: ANTHROPIC_BASE_URL
  });
});

// 根路径
app.get('/', (req, res) => {
  res.json({
    name: 'Anthropic Proxy (Claude Code Impersonator)',
    version: '1.0.0',
    description: '伪装成 Claude Code CLI 的代理服务',
    endpoints: {
      messages: 'POST /v1/messages',
      count_tokens: 'POST /v1/messages/count_tokens',
      health: 'GET /health'
    },
    features: {
      cherry_detection: 'Auto-detect CherryStudio requests',
      system_injection: 'Inject Claude Code identity',
      session_cache: '12-hour rotating session for API cache optimization',
      connection_pool: 'HTTP keep-alive for performance'
    }
  });
});

// 启动服务器
app.listen(PORT, '0.0.0.0', () => {
  console.log('🚀 Anthropic Proxy Started');
  console.log(`📍 Listening: http://0.0.0.0:${PORT}`);
  console.log(`🎭 Spoofing: ${CLAUDE_CODE_HEADERS['user-agent']}`);
  console.log(`🔗 Target: ${ANTHROPIC_BASE_URL}`);
  console.log(`🔑 API Key: ${ANTHROPIC_API_KEY ? 'Configured' : 'From clients'}`);
});
