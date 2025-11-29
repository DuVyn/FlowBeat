"""
应用全局配置模块

本模块使用 Pydantic Settings 管理应用配置，支持:
1. 环境变量注入 (Environment Variables)
2. .env 文件加载 (Dotenv Files)
3. 类型验证和转换 (Type Validation)

设计原则:
1. 配置即代码: 所有配置项都有明确的类型和默认值。
2. 环境感知: 开发、测试、生产环境使用不同的配置值。
3. 安全默认: 敏感配置 (如 SECRET_KEY) 提供开发用默认值，但在生产环境必须覆盖。

加载优先级 (从高到低):
1. 系统环境变量
2. .env 文件
3. 代码中的默认值
"""

from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用全局配置类

    为什么使用 Pydantic Settings:
    1. 类型安全: 配置值自动转换为指定类型，避免字符串类型的配置导致的 Bug。
    2. 验证能力: 可以定义自定义验证器，确保配置值合法。
    3. 文档化: 每个字段都可以添加描述，配置项一目了然。
    4. IDE 支持: 类型注解使 IDE 能提供自动补全和类型检查。
    """

    # =========================================================================
    # 1. 基础项目信息
    # =========================================================================
    # API 版本前缀: 所有 API 路由都会以此为前缀
    # 为什么使用版本前缀: 便于 API 版本管理，支持新旧版本并行运行。
    API_V1_STR: str = "/api/v1"

    # 项目名称: 用于 OpenAPI 文档标题和健康检查响应
    PROJECT_NAME: str = "FlowBeat"

    # =========================================================================
    # 2. 网络与安全 (CORS)
    # =========================================================================
    # CORS 允许的源列表
    # 为什么使用列表而非通配符: 精确控制允许的来源，防止恶意网站发起跨域请求。
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str] | str:
        """
        CORS 源列表预处理器

        为什么需要此验证器:
        环境变量只能传递字符串，但我们需要列表。
        此验证器支持两种格式:
        1. 逗号分隔的字符串: "http://localhost:3000,http://localhost:8080"
        2. JSON 数组格式: ["http://localhost:3000", "http://localhost:8080"]

        Args:
            v: 原始配置值，可能是字符串或列表

        Returns:
            解析后的源列表
        """
        if isinstance(v, str) and not v.startswith("["):
            # 逗号分隔格式: 分割并去除空白
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            # 已经是列表或 JSON 字符串格式，直接返回
            return v
        raise ValueError(v)

    # =========================================================================
    # 3. 数据库 (PostgreSQL)
    # =========================================================================
    # 数据库连接字符串
    #
    # 为什么默认使用 localhost:
    # 本地开发时，数据库通常运行在本机或通过端口映射暴露。
    # Docker 部署时，docker-compose.yml 会通过环境变量注入正确的连接串 (如 host=db)。
    #
    # 为什么使用 asyncpg 驱动:
    # asyncpg 是目前性能最高的 PostgreSQL 异步驱动，比 psycopg2 快 3-5 倍。
    # 配合 SQLAlchemy 2.0 的原生异步支持，可以充分发挥 FastAPI 的异步优势。
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql+asyncpg://flowbeat:flowbeat_dev_pass@localhost:5432/flowbeat_db"
    )

    # =========================================================================
    # 4. 认证与授权 (JWT Authentication)
    # =========================================================================
    # JWT 签名密钥
    # 安全警告: 此默认值仅用于开发环境！生产环境必须通过环境变量设置强随机密钥。
    # 生成方法: openssl rand -hex 32
    SECRET_KEY: str = "TEMPORARY_SECRET_KEY_PLEASE_CHANGE_IN_PRODUCTION"

    # JWT 签名算法
    # 为什么选择 HS256: 对称加密，签名和验证使用同一密钥，适合单体应用。
    # 若需支持微服务架构，应改用 RS256 (非对称加密)，便于公钥分发。
    ALGORITHM: str = "HS256"

    # Access Token 过期时间 (分钟)
    # 为什么设置 11520 分钟 (8 天):
    # 这是开发阶段的宽松设置，减少频繁登录的麻烦。
    # 生产环境建议设为 30-60 分钟，并配合 Refresh Token 机制。
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    # =========================================================================
    # 5. Pydantic 加载策略
    # =========================================================================
    model_config = SettingsConfigDict(
        # .env 文件路径: 相对于项目根目录
        env_file=".env",
        # 文件编码: 支持中文注释
        env_file_encoding="utf-8",
        # 大小写敏感: 环境变量名必须完全匹配
        case_sensitive=True,
        # 忽略额外字段: .env 文件中的未知变量不会导致错误
        extra="ignore",
    )

    # =========================================================================
    # 6. 对象存储 (MinIO / S3)
    # =========================================================================
    # MinIO 服务地址 (如 minio:9000)
    MINIO_ENDPOINT: str = "localhost:9000"
    # Access Key (用户名)
    MINIO_ACCESS_KEY: str = "minioadmin"
    # Secret Key (密码)
    MINIO_SECRET_KEY: str = "minioadmin"
    # 存储桶名称
    MINIO_BUCKET_NAME: str = "flowbeat-music"
    # 是否使用 SSL (本地开发通常为 False)
    MINIO_SECURE: bool = False


# =============================================================================
# 单例实例化
# =============================================================================
# 为什么使用模块级单例:
# 1. 配置在应用启动时加载一次，避免重复解析的开销。
# 2. 所有模块导入 settings 时获得同一实例，确保配置一致性。
# 3. Pydantic Settings 的构造过程包含文件读取和环境变量解析，不应频繁执行。
settings = Settings()
