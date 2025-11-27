from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    所有数据库实体的基类

    1. 统一主键定义。
    2. 自动化表名生成策略。
    """

    # [自动化命名策略]
    # 为什么这么写:
    # 默认表名通常需要手动指定 __tablename__。
    # 这里利用反射机制，将驼峰命名的类名 (如 UserProfile) 自动转换为蛇形表名 (user_profile)。
    # 优势: 减少样板代码，强制统一数据库命名规范。
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # [统一主键]
    # 权衡分析: 使用自增 Int ID 简单高效，适合大多数单体或中小型微服务。
    # 若需分库分表或防遍历，应改用 UUID 或 Snowflake ID。目前阶段 Int 足够。
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
