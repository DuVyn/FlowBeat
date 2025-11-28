"""
用户仓储模块

本模块提供用户实体的数据访问操作，继承自通用 CRUD 仓储基类，
并扩展了用户特有的查询方法。

扩展方法:
1. get_by_email - 根据邮箱查询用户
2. get_by_username - 根据用户名查询用户

使用方式:
    repo = UserRepository()
    user = await repo.get_by_email(db, email="test@example.com")
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    用户仓储层实现

    泛型参数说明:
    - User: 数据库实体类型
    - UserCreate: 创建用户时的请求 Schema
    - UserUpdate: 更新用户时的请求 Schema

    继承关系的优势:
    1. 自动获得 get、get_multi、create、update、remove 等通用方法
    2. 类型系统能正确推断方法参数和返回类型
    3. 只需实现用户特有的查询方法
    """

    def __init__(self) -> None:
        """
        初始化用户仓储

        为什么在这里传入 User:
        运行时父类需要知道具体的 Model 类以便执行 SQL 查询。
        虽然泛型参数中已指定 User，但 Python 泛型在运行时会被擦除，
        因此需要显式传入。
        """
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        根据邮箱查询用户

        使用场景:
        1. 登录验证: 用户使用邮箱登录时查找账户
        2. 注册查重: 检查邮箱是否已被注册
        3. 密码找回: 验证邮箱是否存在

        为什么不使用通用 get 方法:
        通用 get 方法只支持主键查询，而邮箱是业务唯一键，
        需要专门的查询方法。

        Args:
            db: 数据库会话
            email: 用户邮箱

        Returns:
            Optional[User]: 找到则返回用户实体，否则返回 None
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名查询用户

        使用场景:
        1. 登录验证: 用户使用用户名登录时查找账户
        2. 注册查重: 检查用户名是否已被使用
        3. 个人主页: 通过用户名访问用户资料

        性能说明:
        username 字段已建立唯一索引，查询效率为 O(log n)。

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            Optional[User]: 找到则返回用户实体，否则返回 None
        """
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
