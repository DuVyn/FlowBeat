from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.base import BaseRepository


# 1. ModelType -> User (数据库实体)
# 2. CreateSchemaType -> UserCreate (创建时的 Pydantic 模型)
# 3. UpdateSchemaType -> UserUpdate (更新时的 Pydantic 模型)
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    用户仓储层实现

    继承关系确保了 create/update 方法能自动推断出正确的参数类型。
    """

    def __init__(self):
        # 初始化父类，指定 SQLAlchemy 模型为 User
        # 运行时父类需要知道具体的 Model 类以便执行 SQL (select(self.model)...)
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        根据邮箱查询用户

        Args:
            db: 数据库会话
            email: 用户邮箱
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名查询用户
        """
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
