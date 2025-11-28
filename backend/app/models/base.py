"""
数据库模型基类模块

本模块定义了所有数据库实体的基类，提供:
1. 统一的主键定义
2. 自动化的表名生成策略
3. SQLAlchemy 2.0 风格的声明式基类

设计原则:
1. 继承复用: 所有实体继承 Base，自动获得 id 字段和表名生成逻辑
2. 约定优于配置: 通过反射自动生成表名，减少重复代码
3. 类型安全: 使用 Mapped 类型注解，提供完整的类型提示
"""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    所有数据库实体的基类

    为什么需要自定义基类:
    1. 统一主键类型和命名，确保所有表使用相同的主键模式
    2. 自动生成表名，减少样板代码
    3. 未来可以添加通用字段 (如 created_at, updated_at)
    4. 便于添加全局的序列化方法

    继承示例:
        class User(Base):
            # 自动获得 id 主键和表名 "user"
            username: Mapped[str] = mapped_column(String(50))
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        自动化表名生成策略

        为什么使用 declared_attr:
        declared_attr 是 SQLAlchemy 的延迟属性装饰器。
        它允许在子类实例化时动态计算属性值，而非在类定义时。
        这样每个子类都能根据自己的类名生成唯一的表名。

        命名转换规则:
        将驼峰命名的类名转换为小写表名。
        例如: User -> user, UserProfile -> userprofile

        注意事项:
        目前仅做简单的小写转换，不处理驼峰转蛇形。
        如需 UserProfile -> user_profile，需要自定义转换逻辑。

        Returns:
            str: 数据库表名
        """
        return cls.__name__.lower()

    # 统一主键定义
    #
    # 设计权衡:
    # 1. 自增 Int ID: 简单高效，适合单体应用
    #    优点: 存储紧凑、索引效率高、便于调试
    #    缺点: 可被遍历、分库分表困难
    #
    # 2. UUID: 适合分布式系统
    #    优点: 全局唯一、防遍历、无需协调
    #    缺点: 存储占用大、索引效率略低
    #
    # 当前选择: Int ID 作为基类默认值
    # 子类可以覆盖此定义，如 User 模型使用 UUID
    #
    # 为什么设置 index=True:
    # 主键默认有索引，这里显式声明是为了代码可读性
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
