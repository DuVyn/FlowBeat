"""
用户领域模型模块

本模块定义了系统核心的用户实体 (User Entity) 和角色枚举 (UserRole)。
采用领域驱动设计 (DDD) 思想，将用户相关的业务概念封装在此。

设计原则:
1. 实体唯一性: 使用 UUID 作为主键，避免自增 ID 被遍历攻击。
2. 安全存储: 密码字段仅存储哈希值，严禁明文。
3. 软删除: 通过 is_active 字段实现账户禁用，而非物理删除。
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRole(str, Enum):
    """
    用户角色枚举

    为什么继承 str:
    继承 str 使得枚举值可以直接与字符串比较，并且在 JSON 序列化时自动转为字符串，
    避免了额外的转换逻辑。这是 Python 枚举与 Pydantic/FastAPI 配合的最佳实践。

    为什么只定义两个角色:
    遵循最小权限原则 (Principle of Least Privilege)，初始版本仅区分管理员和普通用户。
    未来如需更细粒度的权限控制，可扩展为 RBAC (基于角色的访问控制) 或 ABAC (基于属性的访问控制)。
    """

    ADMIN = "ADMIN"
    USER = "USER"


def _get_utc_now() -> datetime:
    """
    获取当前 UTC 时间

    为什么封装此函数:
    1. Python 3.12+ 中 datetime.utcnow() 已被弃用，推荐使用 datetime.now(timezone.utc)。
    2. SQLAlchemy 的 default 参数需要可调用对象 (callable)，不能直接传入 datetime.now(timezone.utc)。
    3. 统一时间获取逻辑，便于未来进行时间模拟 (Time Mocking) 以支持单元测试。

    Returns:
        datetime: 当前 UTC 时间，带时区信息。
    """
    return datetime.now(timezone.utc)


class User(Base):
    """
    用户领域模型 (User Domain Model)

    采用 SQLAlchemy 2.0 的 Mapped 类型注解风格，映射数据库中的 users 表。

    设计决策:
    1. UUID 主键: 防止 ID 遍历攻击，支持分布式系统。
    2. 双重唯一索引: username 和 email 均建立唯一索引，支持多种登录方式。
    3. 时区感知: 所有时间字段使用 timezone-aware datetime，避免跨时区部署的时间混乱。
    """

    __tablename__ = "users"

    # =========================================================================
    # 主键字段
    # =========================================================================
    # 为什么使用 server_default 而非 Python 端生成:
    # 1. 将 UUID 生成委托给 PostgreSQL，减少 Python 端的计算开销。
    # 2. 利用数据库的 gen_random_uuid() 函数，其随机性由操作系统熵池保证，更加安全。
    # 3. 在批量插入场景下，避免 Python 端成为性能瓶颈。
    #
    # 副作用说明:
    # 在 Python 代码中实例化 User 对象时，id 字段初始为 None。
    # 必须在 session.flush() 或 session.commit() 后，通过 session.refresh() 才能获取生成的 ID。
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True,
    )

    # =========================================================================
    # 业务标识字段
    # =========================================================================
    # 用户名: 业务唯一标识之一
    # 为什么建立索引: 登录时需要根据用户名快速查询，索引可将查询复杂度从 O(n) 降至 O(log n)。
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    # 邮箱: 用于找回密码和作为登录凭证
    # 为什么限制 255 字符: RFC 5321 规定邮箱地址最长为 254 字符，255 提供了安全边界。
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # =========================================================================
    # 安全字段
    # =========================================================================
    # 密码哈希: 存储经过 Argon2id 算法处理后的哈希值
    # 为什么设置 255 长度: Argon2 输出格式包含算法参数、盐值和哈希本体，通常约 100 字符，
    # 预留 255 可兼容未来更强的哈希算法。
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # =========================================================================
    # 个人信息字段
    # =========================================================================
    # 用户全名或昵称: 非核心认证字段，允许为空
    # 为什么允许 None: 注册时可能不需要填写，降低注册门槛。
    full_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # =========================================================================
    # 状态与权限字段
    # =========================================================================
    # 账户启用状态: 用于软删除或封禁逻辑
    # 为什么使用软删除: 保留用户数据用于审计和数据分析，同时满足合规要求。
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # 用户角色: 使用 SQLAlchemy 的 Enum 类型映射 Python 枚举
    # 为什么默认为 USER: 遵循最小权限原则，新注册用户不应自动获得管理员权限。
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"),
        default=UserRole.USER,
        nullable=False,
    )

    # =========================================================================
    # 审计字段
    # =========================================================================
    # 创建时间: 记录账户创建的精确时刻
    # 为什么使用 timezone=True: 存储时区感知的时间戳，避免跨时区部署时的时间偏差。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_get_utc_now,
        nullable=False,
    )

    # 更新时间: 每次记录变更时自动更新
    # 为什么同时设置 default 和 onupdate: 创建时需要初始值，更新时需要自动刷新。
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_get_utc_now,
        onupdate=_get_utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        """
        对象的字符串表示

        为什么重写此方法:
        开发调试时，print(user) 能直接显示关键信息，提高调试效率。
        生产环境中此方法也用于日志记录，注意不要包含敏感信息 (如密码哈希)。
        """
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
