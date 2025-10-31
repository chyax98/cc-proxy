"""
适配器管理器

负责注册、检测和应用客户端适配器
使用统一的 common.adapters 接口
"""

from common.adapters import AdapterContext, ClientAdapter, DefaultAdapter, TransformResult
from common.logger import get_logger

from .cherry_studio import CherryStudioAdapter
from .claude_code import ClaudeCodeAdapter

logger = get_logger(__name__)


class AdapterManager:
    """适配器管理器 (统一接口)"""

    def __init__(self) -> None:
        """初始化适配器管理器并注册默认适配器"""
        self._adapters: list[ClientAdapter] = []
        self._default_adapter = DefaultAdapter()
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """注册默认适配器"""
        self.register(ClaudeCodeAdapter())    # 优先级 100 (官方客户端)
        self.register(CherryStudioAdapter())  # 优先级 50 (第三方客户端)
        logger.info("registered_default_adapters", count=len(self._adapters))

    def register(self, adapter: ClientAdapter) -> None:
        """
        注册适配器

        Args:
            adapter: 客户端适配器实例
        """
        self._adapters.append(adapter)
        # 按优先级排序 (优先级高的先匹配)
        self._adapters.sort(key=lambda a: a.priority, reverse=True)
        logger.info(
            "adapter_registered",
            name=adapter.name,
            version=adapter.version,
            priority=adapter.priority,
        )

    def select_adapter(self, ctx: AdapterContext) -> ClientAdapter:
        """
        选择匹配的适配器

        Args:
            ctx: 适配器上下文

        Returns:
            匹配的适配器 (如果没有匹配则返回默认适配器)
        """
        for adapter in self._adapters:
            if adapter.detect(ctx):
                logger.info("adapter_selected", adapter=adapter.name)
                return adapter

        logger.info("using_default_adapter")
        return self._default_adapter

    def transform(self, ctx: AdapterContext) -> TransformResult:
        """
        应用适配器转换

        Args:
            ctx: 适配器上下文

        Returns:
            转换结果 (包含 body + extra_headers + metadata)
        """
        adapter = self.select_adapter(ctx)
        result = adapter.transform(ctx)

        logger.info(
            "request_transformed",
            adapter=adapter.name,
            extra_headers_count=len(result.extra_headers),
        )

        return result

    def list_adapters(self) -> list[dict[str, str | int]]:
        """
        列出所有已注册的适配器

        Returns:
            适配器信息列表 (包含 name, version, priority)
        """
        return [
            {
                "name": adapter.name,
                "version": adapter.version,
                "priority": adapter.priority,
            }
            for adapter in self._adapters
        ]


# 全局适配器管理器实例
adapter_manager = AdapterManager()
