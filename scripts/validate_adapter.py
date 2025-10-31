#!/usr/bin/env python3
"""
Codex Adapter 快速验证脚本

用法:
    uv run python scripts/validate_adapter.py
    或
    cd /path/to/cc_cx-proxy && uv run scripts/validate_adapter.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入日志系统
from common.logger import get_logger

logger = get_logger(__name__)

try:
    # 导入时需要注意 service-cx 的包名是带连字符的
    import importlib.util

    # 动态加载 service-cx 模块
    service_cx_path = project_root / "service-cx"

    # 导入 common 模块
    from common.adapters import AdapterContext

    # 动态导入 CherryStudioAdapter
    spec = importlib.util.spec_from_file_location(
        "cherry_studio_adapter",
        service_cx_path / "adapters" / "cherry_studio.py"
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        CherryStudioAdapter = module.CherryStudioAdapter
    else:
        raise ImportError("无法加载 CherryStudioAdapter")

except (ModuleNotFoundError, ImportError) as e:
    logger.error("module_import_failed", error=str(e))
    logger.error("usage_instructions",
                 usage1="cd /path/to/cc_cx-proxy",
                 usage2="uv run python scripts/validate_adapter.py")
    sys.exit(1)


def validate_detection():
    """验证检测逻辑"""
    logger.info("validation_test_1_detection")
    adapter = CherryStudioAdapter()

    # 测试 CherryStudio UA
    ctx = AdapterContext(
        raw_body={},
        raw_headers={"user-agent": "CherryStudio/1.6.5"},
    )
    assert adapter.detect(ctx) is True
    logger.info("cherry_studio_detection_success")

    # 测试非 CherryStudio UA
    ctx = AdapterContext(
        raw_body={},
        raw_headers={"user-agent": "codex_cli_rs/0.50.0"},
    )
    assert adapter.detect(ctx) is False
    logger.info("other_ua_detection_success")


def validate_transformation():
    """验证转换逻辑"""
    logger.info("validation_test_2_transformation")
    adapter = CherryStudioAdapter()

    ctx = AdapterContext(
        raw_body={
            "model": "gpt-5-codex",
            "input": [{"role": "user", "content": "Hello"}],
            "reasoning": {"effort": "high"},
        },
        raw_headers={"user-agent": "CherryStudio/1.6.5"},
    )

    result = adapter.transform(ctx)

    # 验证关键字段
    assert result.body["model"] == "gpt-5-codex"
    assert "instructions" in result.body
    assert len(result.body["input"]) >= 1
    assert len(result.body["tools"]) == 7
    assert result.body["reasoning"]["effort"] == "high"
    assert "conversation_id" in result.extra_headers

    logger.info("model_field_correct")
    logger.info("instructions_injected_successfully")
    logger.info("input_transformed_successfully")
    logger.info("tools_merged_successfully", count=len(result.body['tools']))
    logger.info("reasoning_configured_correctly")
    logger.info("extra_headers_generated_successfully")


def validate_session_rotation():
    """验证 Session 轮换"""
    logger.info("validation_test_3_session_rotation")

    # 动态导入 session 模块
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "session",
        project_root / "service-cx" / "formats" / "session.py"
    )
    if spec and spec.loader:
        session_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(session_module)
        codex_session_manager = session_module.codex_session_manager

        codex_session_manager.clear_cache()

        id1 = codex_session_manager.get_identifiers()
        id2 = codex_session_manager.get_identifiers()

        assert id1["conversation_id"] == id2["conversation_id"]
        logger.info("session_reuse_correct")
    else:
        logger.warning("session_module_load_failed_test_skipped")


def main():
    """运行所有验证"""
    logger.info("starting_codex_adapter_validation")

    try:
        validate_detection()
        validate_transformation()
        validate_session_rotation()

        logger.info("all_validations_passed_successfully")
        return 0

    except AssertionError as e:
        logger.error("validation_failed", error=str(e))
        return 1
    except Exception as e:
        logger.error("execution_error", error=str(e), error_type=type(e).__name__)
        import traceback
        logger.error("execution_traceback", traceback=traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
