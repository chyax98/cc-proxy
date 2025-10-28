import type { RequestBody, RequestHeaders, PluginInfo } from '../types.js';

/**
 * 插件基类 - 定义协议转换插件的标准接口
 */
export abstract class ProtocolPlugin {
  /**
   * 插件名称
   */
  abstract readonly name: string;

  /**
   * 插件版本
   */
  abstract readonly version: string;

  /**
   * 插件描述
   */
  abstract readonly description: string;

  /**
   * 检测是否应该使用此插件处理请求
   */
  abstract detect(body: RequestBody, headers: RequestHeaders): boolean;

  /**
   * 转换请求体
   */
  abstract transform(body: RequestBody, headers: RequestHeaders): RequestBody;

  /**
   * 获取目标请求头
   */
  abstract getHeaders(apiKey: string): RequestHeaders;

  /**
   * 插件初始化（可选）
   */
  initialize?(): void | Promise<void>;

  /**
   * 插件销毁（可选）
   */
  destroy?(): void | Promise<void>;

  /**
   * 获取插件信息
   */
  getInfo(): PluginInfo {
    return {
      name: this.name,
      version: this.version,
      description: this.description
    };
  }
}
