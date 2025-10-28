/**
 * 核心类型定义
 */

export interface RequestBody {
  model: string;
  messages: Message[];
  system?: SystemBlock[];
  tools?: Tool[];
  metadata?: Metadata;
  stream?: boolean;
  thinking?: unknown;
  [key: string]: unknown;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string | MessageContent[];
}

export interface MessageContent {
  type: string;
  text?: string;
  [key: string]: unknown;
}

export interface SystemBlock {
  type: string;
  text?: string;
  cache_control?: CacheControl;
  [key: string]: unknown;
}

export interface CacheControl {
  type: 'ephemeral';
}

export interface Tool {
  name: string;
  description?: string;
  input_schema?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Metadata {
  user_id?: string;
  [key: string]: unknown;
}

export interface RequestHeaders {
  'user-agent'?: string;
  'authorization'?: string;
  'x-api-key'?: string;
  'anthropic-api-key'?: string;
  'content-type'?: string;
  [key: string]: string | undefined;
}

export interface PluginResult {
  body: RequestBody;
  getHeaders: (apiKey: string) => RequestHeaders;
  plugin: PluginInfo;
}

export interface PluginInfo {
  name: string;
  version: string;
  description?: string;
}
