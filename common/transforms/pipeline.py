"""
转换管道

按顺序执行多个转换器
"""

from __future__ import annotations

import copy
from typing import Any

from common.logger import get_logger

from .base import TransformContext, Transformer

logger = get_logger(__name__)


class TransformError(Exception):
    """转换错误"""

    pass


class TransformPipeline:
    """
    转换管道

    按顺序执行一系列转换器，实现复杂的转换流程
    """

    def __init__(self, transformers: list[Transformer]):
        """
        初始化管道

        Args:
            transformers: 转换器列表（按执行顺序）
        """
        self.transformers = transformers

    def execute(self, data: dict[str, Any], context: TransformContext) -> dict[str, Any]:
        """
        执行管道转换

        Args:
            data: 原始数据
            context: 转换上下文

        Returns:
            转换后的数据

        Raises:
            TransformError: 转换失败
        """
        # 深拷贝避免修改原始数据
        result = copy.deepcopy(data)

        logger.info(
            "pipeline_start",
            target_api=context.target_api,
            client_type=context.client_type,
            transformer_count=len(self.transformers),
        )

        for transformer in self.transformers:
            try:
                # 执行转换
                result = transformer.transform(result, context)

                # 验证结果
                if not transformer.validate(result):
                    raise TransformError(
                        f"Validation failed in transformer: {transformer.name}"
                    )

                logger.debug(
                    "transformer_executed",
                    transformer=transformer.name,
                )

            except Exception as e:
                logger.error(
                    "transformer_error",
                    transformer=transformer.name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise TransformError(
                    f"Transformer '{transformer.name}' failed: {e}"
                ) from e

        logger.info("pipeline_complete")
        return result


__all__ = ["TransformPipeline", "TransformError"]
