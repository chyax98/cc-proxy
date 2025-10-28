import { ProtocolPlugin } from './base.js';
import type { RequestBody, RequestHeaders, PluginResult, PluginInfo } from '../types.js';

/**
 * 插件管理器 - 负责插件注册、加载和调度
 */
export class PluginManager {
  private plugins = new Map<string, ProtocolPlugin>();
  private activePlugins: ProtocolPlugin[] = [];

  /**
   * 注册插件
   */
  async register(plugin: ProtocolPlugin): Promise<void> {
    if (!plugin.name) {
      throw new Error('Plugin must have a name');
    }

    if (this.plugins.has(plugin.name)) {
      throw new Error(`Plugin "${plugin.name}" already registered`);
    }

    this.plugins.set(plugin.name, plugin);
    this.activePlugins.push(plugin);

    // 初始化插件
    if (plugin.initialize) {
      await plugin.initialize();
    }

    console.log(`✅ Plugin registered: ${plugin.name} v${plugin.version}`);
  }

  /**
   * 注销插件
   */
  async unregister(name: string): Promise<boolean> {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      return false;
    }

    // 销毁插件
    if (plugin.destroy) {
      await plugin.destroy();
    }

    this.plugins.delete(name);
    this.activePlugins = this.activePlugins.filter(p => p.name !== name);

    console.log(`❌ Plugin unregistered: ${name}`);
    return true;
  }

  /**
   * 查找匹配的插件
   */
  findPlugin(body: RequestBody, headers: RequestHeaders): ProtocolPlugin | null {
    for (const plugin of this.activePlugins) {
      if (plugin.detect(body, headers)) {
        return plugin;
      }
    }
    return null;
  }

  /**
   * 处理请求（自动匹配插件）
   */
  process(body: RequestBody, headers: RequestHeaders): PluginResult | null {
    const plugin = this.findPlugin(body, headers);
    if (!plugin) {
      return null;
    }

    const transformedBody = plugin.transform(body, headers);
    const getHeaders = (apiKey: string) => plugin.getHeaders(apiKey);

    return {
      body: transformedBody,
      getHeaders,
      plugin: plugin.getInfo()
    };
  }

  /**
   * 获取所有已注册插件信息
   */
  list(): PluginInfo[] {
    return Array.from(this.plugins.values()).map(p => p.getInfo());
  }

  /**
   * 获取插件数量
   */
  get size(): number {
    return this.plugins.size;
  }

  /**
   * 销毁所有插件
   */
  async destroyAll(): Promise<void> {
    for (const plugin of this.activePlugins) {
      if (plugin.destroy) {
        await plugin.destroy();
      }
    }
    this.plugins.clear();
    this.activePlugins = [];
  }
}
