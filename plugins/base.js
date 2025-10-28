/**
 * 插件基类 - 定义协议转换插件的标准接口
 */
export class ProtocolPlugin {
  /**
   * 插件名称
   * @type {string}
   */
  name = 'BasePlugin';

  /**
   * 插件版本
   * @type {string}
   */
  version = '1.0.0';

  /**
   * 插件描述
   * @type {string}
   */
  description = 'Base protocol conversion plugin';

  /**
   * 检测是否应该使用此插件处理请求
   * @param {Object} body - 请求体
   * @param {Object} headers - 请求头
   * @returns {boolean}
   */
  detect(body, headers) {
    throw new Error('detect() must be implemented by subclass');
  }

  /**
   * 转换请求体
   * @param {Object} body - 原始请求体
   * @param {Object} headers - 原始请求头
   * @returns {Object} 转换后的请求体
   */
  transform(body, headers) {
    throw new Error('transform() must be implemented by subclass');
  }

  /**
   * 获取目标请求头
   * @param {string} apiKey - API密钥
   * @returns {Object} 请求头对象
   */
  getHeaders(apiKey) {
    throw new Error('getHeaders() must be implemented by subclass');
  }

  /**
   * 插件初始化（可选）
   */
  initialize() {
    // 子类可以覆盖此方法进行初始化
  }

  /**
   * 插件销毁（可选）
   */
  destroy() {
    // 子类可以覆盖此方法进行清理
  }
}
