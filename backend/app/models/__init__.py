"""
数据库模型包

本包包含所有 SQLAlchemy ORM 模型定义。

模型导出说明:
此处显式导出所有模型类，这对于 Alembic 自动生成迁移脚本至关重要。
如果不在此处导入模型，Alembic 的 env.py 可能无法通过 target_metadata 发现这些表结构。

"""

from app.models.base import Base
from app.models.user import User
from app.models.music import Album, Artist, Music
from app.models.interaction import Interaction, InteractionType, INTERACTION_WEIGHTS

__all__ = ["Base", "User", "Artist", "Album", "Music", "Interaction", "InteractionType", "INTERACTION_WEIGHTS"]
