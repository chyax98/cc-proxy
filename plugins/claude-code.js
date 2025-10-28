import { ProtocolPlugin } from './base.js';

/**
 * Claude Code 协议插件
 * 将 CherryStudio 等第三方客户端的请求伪装成 Claude Code CLI
 */
export class ClaudeCodePlugin extends ProtocolPlugin {
  name = 'ClaudeCode';
  version = '1.0.0';
  description = 'Transform requests to Claude Code CLI format';

  // Claude Code system 模板
  static SYSTEM_TEMPLATE = [
    {
      type: 'text',
      text: 'You are Claude Code, Anthropic\'s official CLI for Claude.',
      cache_control: {
        type: 'ephemeral'
      }
    }
  ];

  // Claude Code 请求头特征（基于官方 2.0.24 版本）
  static HEADERS = {
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

  // Session 缓存
  cachedSession = null;
  sessionExpireTime = 0;
  SESSION_TTL = 12 * 60 * 60 * 1000; // 12小时

  /**
   * 检测是否为需要转换的请求
   */
  detect(body, headers) {
    const userAgent = headers['user-agent'] || '';

    // 特征1: User-Agent包含CherryStudio
    const hasCherryUA = userAgent.includes('CherryStudio');

    // 特征2: tools字段缺失或为空
    const hasNoTools = !body.tools || body.tools.length === 0;

    // 特征3: system不包含"You are Claude Code"
    const notClaudeCode = !body.system?.some(s =>
      s.text?.includes('You are Claude Code')
    );

    return hasCherryUA || (hasNoTools && notClaudeCode);
  }

  /**
   * 转换请求体
   */
  transform(body, headers) {
    // 1. 替换system字段为Claude Code格式
    body.system = ClaudeCodePlugin.SYSTEM_TEMPLATE;

    // 2. 添加metadata（优先复用，否则使用12小时轮换session）
    if (!body.metadata?.user_id) {
      body.metadata = this.generateMetadata();
    }

    // 3. 移除Cherry特有的thinking字段
    if (body.thinking) {
      delete body.thinking;
    }

    return body;
  }

  /**
   * 获取目标请求头
   */
  getHeaders(apiKey) {
    return {
      ...ClaudeCodePlugin.HEADERS,
      'authorization': `Bearer ${apiKey}`
    };
  }

  /**
   * 生成metadata（12小时轮换session）
   */
  generateMetadata() {
    const now = Date.now();

    // 如果session未过期，复用
    if (this.cachedSession && now < this.sessionExpireTime) {
      return this.cachedSession;
    }

    // 生成新session
    const timestamp = new Date().toISOString().split('T')[0];
    const halfDayMark = Math.floor(now / this.SESSION_TTL);
    const sessionId = `88code-cherry-${timestamp}-${halfDayMark}`;

    this.cachedSession = {
      user_id: `user_88code_proxy_account__session_${sessionId}`
    };
    this.sessionExpireTime = now + this.SESSION_TTL;

    return this.cachedSession;
  }
}
