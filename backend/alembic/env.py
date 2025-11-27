import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# -----------------------------------------------------------------------------
# [架构修正] 动态注入项目根路径
# -----------------------------------------------------------------------------
# 问题背景:
# Alembic 作为一个独立工具运行，默认不在 backend 目录下。
# 当代码中尝试 `from app.core import ...` 时，Python 解释器会报 ModuleNotFoundError。
# 解决方案:
# 计算当前文件的祖父目录 (即 backend/) 并动态加入 sys.path，确保模块解析正常。
# -----------------------------------------------------------------------------
base_path = Path(__file__).resolve().parent.parent
sys.path.append(str(base_path))

# 导入项目配置和所有模型基类
from app.core.config import settings
from app.models.base import Base

# 读取 alembic.ini 配置
config = context.config

# 初始化日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据，用于自动生成迁移脚本
target_metadata = Base.metadata

# 强制使用配置类中的数据库 URL (覆盖 alembic.ini 中的占位符)
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))


def run_migrations_offline() -> None:
    """离线迁移模式 (生成 SQL 脚本)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的具体逻辑 (同步包装器)"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    在线迁移模式 (异步连接)

    [技术难点解决]
    Alembic 核心是同步的，但我们的 settings 配置了 asyncpg (异步驱动)。
    这里我们创建一个异步 Engine，获取连接后，使用 `run_sync` 方法
    将同步的 `do_run_migrations` 函数投递到事件循环中执行。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
