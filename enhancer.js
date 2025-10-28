// 内联Claude Code模板（避免文件I/O开销）
// System模板：仅包含身份声明 + 缓存控制（121字符）
const CLAUDE_CODE_SYSTEM = [
  {
    type: 'text',
    text: 'You are Claude Code, Anthropic\'s official CLI for Claude.',
    cache_control: {
      type: 'ephemeral'
    }
  }
];

/**
 * 生成metadata.user_id（模拟Claude Code格式）
 * 每12小时轮换一次session，平衡缓存利用和session多样性
 */
let cachedSession = null;
let sessionExpireTime = 0;
const SESSION_TTL = 12 * 60 * 60 * 1000; // 12小时（毫秒）

function generateMetadata() {
  const now = Date.now();

  // 如果session未过期，复用
  if (cachedSession && now < sessionExpireTime) {
    return cachedSession;
  }

  // 生成新session（12小时有效期）
  const timestamp = new Date().toISOString().split('T')[0]; // 2025-10-29
  const halfDayMark = Math.floor(now / SESSION_TTL); // 每12小时变化
  const sessionId = `88code-cherry-${timestamp}-${halfDayMark}`;

  cachedSession = {
    user_id: `user_88code_proxy_account__session_${sessionId}`
  };
  sessionExpireTime = now + SESSION_TTL;

  return cachedSession;
}

/**
 * 检测是否为Cherry请求
 */
function isCherryRequest(body, headers) {
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
 * 增强Cherry请求，伪装成Claude Code CLI
 * @param {Object} body - 请求体
 * @param {Object} headers - 请求头
 * @returns {Object} 增强后的请求体
 */
export function enhanceCherryRequest(body, headers) {
  // 检测是否为Cherry请求
  if (!isCherryRequest(body, headers)) {
    return body;
  }

  // 1. 替换system字段为Claude Code格式
  body.system = CLAUDE_CODE_SYSTEM;

  // 2. 添加metadata（优先复用Cherry的，否则使用12小时轮换session）
  if (!body.metadata?.user_id) {
    body.metadata = generateMetadata();
  }

  // 3. 移除Cherry特有的thinking字段
  if (body.thinking) {
    delete body.thinking;
  }

  return body;
}
