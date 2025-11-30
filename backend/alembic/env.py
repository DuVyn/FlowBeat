"""
Alembic 数据库迁移环境配置

本模块配置 Alembic 的运行环境，支持:
1. 异步数据库连接 (asyncpg)
2. 动态加载项目配置
3. 自动发现 ORM 模型

使用方式:
    # 生成迁移脚本
    alembic revision --autogenerate -m "Add new table"

    # 执行迁移
    alembic upgrade head

    # 回滚迁移
    alembic downgrade -1
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# =============================================================================
# 项目路径注入
# =============================================================================
# 为什么需要动态注入路径:
# Alembic 作为一个独立工具运行，其工作目录可能不在 backend/ 下。
# 当代码中尝试 `from app.core import ...` 时，Python 解释器会报 ModuleNotFoundError。
#
# 解决方案:
# 计算当前文件的祖父目录 (即 backend/) 并动态加入 sys.path。
# Path(__file__).resolve().parent.parent 的解析:
#   __file__ = alembic/env.py
#   parent    = alembic/
#   parent    = backend/
base_path = Path(__file__).resolve().parent.parent
sys.path.append(str(base_path))

# 导入项目配置和模型基类
# 必须在路径注入之后导入
from app.core.config import settings
# 从 app.models 包导入以触发所有模型的加载
# 这确保 Alembic 能发现所有在 app/models/__init__.py 中导出的模型
from app.models import Base

# =============================================================================
# Alembic 配置初始化
# =============================================================================
# 读取 alembic.ini 配置
config = context.config

# 初始化日志
# 使用 alembic.ini 中定义的日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
# Alembic 通过此元数据发现所有 ORM 模型，用于自动生成迁移脚本
# 确保所有模型都在 app.models.__init__.py 中导入
target_metadata = Base.metadata

# 覆盖数据库 URL
# 使用项目配置中的 URL，而非 alembic.ini 中的占位符
# 这确保了与应用使用相同的数据库连接配置
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))


def run_migrations_offline() -> None:
    """
    离线迁移模式

    用途:
    生成 SQL 脚本而不实际执行，适用于:
    1. 需要人工审核 SQL 的生产环境
    2. 数据库不可直接访问的情况
    3. 需要将迁移脚本交给 DBA 执行

    运行方式:
        alembic upgrade head --sql > migration.sql
    """
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
    """
    执行迁移的核心逻辑

    为什么需要单独封装:
    Alembic 的核心逻辑是同步的，而我们使用异步数据库连接。
    通过 run_sync 方法，可以在异步上下文中执行同步代码。

    Args:
        connection: 同步数据库连接对象
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    在线迁移模式 (异步)

    技术实现:
    1. 创建异步数据库引擎
    2. 获取异步连接
    3. 使用 run_sync 在连接上执行同步迁移逻辑
    4. 完成后释放连接

    为什么使用 NullPool:
    迁移是一次性操作，不需要连接池的复用特性。
    NullPool 确保每次请求都创建新连接，执行完立即释放。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# =============================================================================
# 模式选择与执行
# =============================================================================
if context.is_offline_mode():
    # 离线模式: 生成 SQL 脚本
    run_migrations_offline()
else:
    # 在线模式: 直接执行迁移
    asyncio.run(run_migrations_online())
