"""
共享配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    # 服务配置
    app_name: str = "CC_CX_Proxy"
    app_version: str = "1.0.0"
    debug: bool = False

    # 环境配置 (production/test)
    # production: 生产环境,不记录详细日志
    # test: 测试环境,记录详细请求/响应体
    environment: str = "production"

    # Claude Service 配置
    claude_service_host: str = "0.0.0.0"
    claude_service_port: int = 8001

    # Codex Service 配置
    codex_service_host: str = "0.0.0.0"
    codex_service_port: int = 8002

    # 外部 API 配置
    anthropic_base_url: str = "https://api.anthropic.com"  # 可通过环境变量覆盖
    openai_base_url: str = "https://api.openai.com/v1"     # 可通过环境变量覆盖

    # 调试配置
    codex_dump_requests: bool = False
    codex_dump_dir: str = "/tmp"

    # Codex 环境上下文默认值
    codex_env_cwd: str = "/home/user"  # 可通过环境变量覆盖
    codex_env_approval_policy: str = "on-request"
    codex_env_sandbox_mode: str = "read-only"
    codex_env_network_access: str = "restricted"
    codex_env_shell: str = "bash"

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    @property
    def is_test_environment(self) -> bool:
        """判断是否为测试环境"""
        return self.environment.lower() in ("test", "dev", "development")

    # HTTP 客户端配置
    http_timeout: float = 120.0
    http_connect_timeout: float = 10.0
    http_max_keepalive: int = 100
    http_max_connections: int = 200
    http_keepalive_expiry: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
