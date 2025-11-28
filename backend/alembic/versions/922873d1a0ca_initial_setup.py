"""
数据库迁移脚本: 初始设置

本迁移脚本由 Alembic 自动生成于初始化阶段。
当前为空迁移，实际表结构由后续迁移脚本定义。

Revision ID: 922873d1a0ca
Revises: 无 (初始迁移)
Create Date: 2025-11-27 21:06:16.145406

使用说明:
    升级: alembic upgrade 922873d1a0ca
    降级: alembic downgrade -1
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# =============================================================================
# Alembic 版本标识
# =============================================================================
# revision: 当前迁移的唯一标识
# down_revision: 前一个迁移的标识，None 表示这是第一个迁移
# branch_labels: 分支标签，用于多分支迁移场景
# depends_on: 依赖的其他迁移
revision: str = "922873d1a0ca"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    升级迁移

    执行数据库模式变更，将数据库升级到此版本。
    当前为初始化迁移，无需执行任何操作。
    """
    pass


def downgrade() -> None:
    """
    降级迁移

    回滚数据库模式变更，将数据库降级到前一版本。
    当前为初始化迁移，无需执行任何操作。
    """
    pass
