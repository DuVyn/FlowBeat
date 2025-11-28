# 显式导出所有模型，这对于 Alembic 自动生成迁移脚本至关重要。
# 如果不在此处导入，Alembic 的 env.py 可能无法通过 target_metadata 发现这些表结构。

from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
