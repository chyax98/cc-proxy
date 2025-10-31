"""
公共转换器库

提供可复用的转换组件，用于适配器转换管道
"""

from .base import TransformContext, Transformer
from .environment_context import EnvironmentContextTransformer
from .field_resolver import FieldResolverTransformer
from .message_normalizer import MessageNormalizerTransformer
from .pipeline import TransformPipeline
from .session import SessionTransformer
from .system_prompt import SystemPromptTransformer
from .tools_merger import ToolsMergerTransformer

__all__ = [
    # 基础类
    "Transformer",
    "TransformContext",
    "TransformPipeline",
    # 转换器
    "SystemPromptTransformer",
    "MessageNormalizerTransformer",
    "ToolsMergerTransformer",
    "SessionTransformer",
    "FieldResolverTransformer",
    "EnvironmentContextTransformer",
]
