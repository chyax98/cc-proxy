/**
 * 插件管理器 - 负责插件注册、加载和调度
 */
export class PluginManager {
  constructor() {
    this.plugins = new Map();
    this.activePlugins = [];
  }

  /**
   * 注册插件
   * @param {ProtocolPlugin} plugin - 插件实例
   */
  register(plugin) {
    if (!plugin.name) {
      throw new Error('Plugin must have a name');
    }

    if (this.plugins.has(plugin.name)) {
      throw new Error(`Plugin "${plugin.name}" already registered`);
    }

    this.plugins.set(plugin.name, plugin);
    this.activePlugins.push(plugin);

    // 初始化插件
    if (typeof plugin.initialize === 'function') {
      plugin.initialize();
    }

    console.log(`✅ Plugin registered: ${plugin.name} v${plugin.version}`);
  }

  /**
   * 注销插件
   * @param {string} name - 插件名称
   */
  unregister(name) {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      return false;
    }

    // 销毁插件
    if (typeof plugin.destroy === 'function') {
      plugin.destroy();
    }

    this.plugins.delete(name);
    this.activePlugins = this.activePlugins.filter(p => p.name !== name);

    console.log(`❌ Plugin unregistered: ${name}`);
    return true;
  }

  /**
   * 查找匹配的插件
   * @param {Object} body - 请求体
   * @param {Object} headers - 请求头
   * @returns {ProtocolPlugin|null}
   */
  findPlugin(body, headers) {
    for (const plugin of this.activePlugins) {
      if (plugin.detect(body, headers)) {
        return plugin;
      }
    }
    return null;
  }

  /**
   * 处理请求（自动匹配插件）
   * @param {Object} body - 请求体
   * @param {Object} headers - 请求头
   * @returns {Object|null} { body, getHeaders } 或 null（无匹配插件）
   */
  process(body, headers) {
    const plugin = this.findPlugin(body, headers);
    if (!plugin) {
      return null;
    }

    const transformedBody = plugin.transform(body, headers);
    const getHeaders = (apiKey) => plugin.getHeaders(apiKey);

    return {
      body: transformedBody,
      getHeaders,
      plugin: {
        name: plugin.name,
        version: plugin.version
      }
    };
  }

  /**
   * 获取所有已注册插件信息
   */
  list() {
    return Array.from(this.plugins.values()).map(p => ({
      name: p.name,
      version: p.version,
      description: p.description
    }));
  }

  /**
   * 销毁所有插件
   */
  destroyAll() {
    for (const plugin of this.activePlugins) {
      if (typeof plugin.destroy === 'function') {
        plugin.destroy();
      }
    }
    this.plugins.clear();
    this.activePlugins = [];
  }
}
