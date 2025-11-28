from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用全局配置类
    """

    # =========================================================================
    # 1. 基础项目信息
    # =========================================================================
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FlowBeat"

    # =========================================================================
    # 2. 网络与安全 (CORS)
    # =========================================================================
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # =========================================================================
    # 3. 数据库 (PostgreSQL)
    # =========================================================================
    # [关键修复] 修改默认 host 为 localhost
    # 原值: "postgresql+asyncpg://postgres:postgres@db:5432/flowbeat" (适用于 Docker 内部)
    # 新值: "postgresql+asyncpg://postgres:postgres@localhost:5432/flowbeat" (适用于本地开发)
    #
    # [架构设计] 环境适应性
    # 1. 本地调试时，使用默认值 localhost，直连本地端口映射的数据库。
    # 2. Docker 部署时，docker-compose.yml 会通过环境变量 SQLALCHEMY_DATABASE_URI
    #    注入含有 host 'db' 的连接串，覆盖此处的默认值。
    SQLALCHEMY_DATABASE_URI: str = "postgresql+asyncpg://flowbeat:flowbeat_dev_pass@localhost:5432/flowbeat"

    # =========================================================================
    # 4. 认证与授权 (JWT Authentication)
    # =========================================================================
    SECRET_KEY: str = "TEMPORARY_SECRET_KEY_PLEASE_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    # =========================================================================
    # 5. Pydantic 加载策略
    # =========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra="ignore"
    )


# 实例化单例
settings = Settings()
