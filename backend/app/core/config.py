# [设计意图]
# 1. 类型安全: 将字符串类型的环境变量自动转换为 int, bool, list 等 Python 类型。
# 2. 集中管理: 避免在业务代码中散落 os.getenv() 调用，消除"魔术字符串"。
# 3. 快速失败 (Fail-Fast): 启动时若关键配置缺失，立即崩溃，避免带病运行。
# =============================================================================

from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置类 (单例模式使用)
    """

    # [Pydantic 配置]
    # case_sensitive=True: 环境变量严格区分大小写，符合 Linux 规范。
    # extra="ignore": 忽略 .env 中未定义的字段。
    # 权衡分析: 选择 ignore 而不是 forbid，是因为容器环境中常注入无关的系统变量(如 HOSTNAME)，
    # 强制禁止会导致容器启动失败。
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # --- 1. 项目元数据 ---
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    # 生产环境必须修改此密钥，用于 JWT 签名加密
    SECRET_KEY: str

    # --- 2. 安全与跨域 (CORS) ---
    # 定义允许跨域访问的前端域名列表
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        验证器: 解析环境变量中的 JSON 字符串或逗号分隔字符串为 List 对象。
        为何这样做: .env 文件只支持字符串，而代码中需要列表结构进行逻辑判断。
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- 3. 数据库 (PostgreSQL) ---
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """
        [计算属性] 动态生成 SQLAlchemy 连接字符串。
        为何使用 computed_field:
        1. 保持 .env 简洁，只需配置基础字段(host, port等)。
        2. 确保使用 'postgresql+asyncpg' 协议头，强制启用异步驱动。
        """
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=f"{self.POSTGRES_DB}",
        )

    # --- 4. 缓存与消息队列 (Redis) ---
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """
        [计算属性] 生成 Redis 连接字符串。
        用于 Celery Broker 和 Redis Client 初始化。
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # --- 5. 对象存储 (MinIO) ---
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_SECURE: bool = False


# 实例化单例对象，供全项目引用
settings = Settings()
