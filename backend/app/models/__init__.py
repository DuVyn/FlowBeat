"""
数据库模型包

本包包含所有 SQLAlchemy ORM 模型定义。

模型导出说明:
此处显式导出所有模型类，这对于 Alembic 自动生成迁移脚本至关重要。
如果不在此处导入模型，Alembic 的 env.py 可能无法通过 target_metadata 发现这些表结构。

当前导出的模型:
- Base: 所有模型的基类
- User: 用户实体

扩展指南:
新增模型时，需要:
1. 在本包下创建新的模型文件 (如 music.py)
2. 在此文件中导入并添加到 __all__ 列表
"""

from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
