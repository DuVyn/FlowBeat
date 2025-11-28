import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

from app.models.base import Base


# 定义角色枚举，用于 RBAC 权限控制
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    """
    用户领域模型 (User Domain Model)

    采用 SQLAlchemy 2.0 的 Mapped 类型注解风格，
    映射数据库中的 'users' 表。
    """
    __tablename__ = "users"

    # [架构决策 - ID 生成策略]
    # 使用 server_default 指示 PostgreSQL 数据库使用内置函数 gen_random_uuid() 生成主键。

    # 副作用说明: 在 Python 代码中实例化 User 对象时，id 字段初始为 None。
    # 必须在 session.flush() 或 session.commit() 后，通过 session.refresh() 才能获取生成的 ID。
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )

    # 用户名，业务唯一标识之一，建立唯一索引以保证数据一致性
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    # 邮箱，用于找回密码或作为登录凭证
    # 同样需要唯一索引约束
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # 存储哈希处理后的密码，严禁存储明文
    # 长度设为 255 以兼容未来可能更长的哈希算法 (如 Argon2)
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 用户全名或昵称，非核心认证字段，允许为空
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 账户启用状态，用于软删除或封禁逻辑
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 角色字段，使用 SQLAlchemy 的 Enum 类型映射 Python 枚举
    # 默认为普通用户，确保最小权限原则
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"),
        default=UserRole.USER,
        nullable=False
    )

    # 记录创建时间，自动处理
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # 记录最后更新时间，每次 update 时自动更新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        # 开发调试时的对象字符串表示
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
