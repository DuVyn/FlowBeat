from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.models.user import User


class AuthService:
    """
    认证领域服务 (Domain Service)

    [职责]
    负责处理登录验证、用户注册、Token 签发等涉及业务规则的逻辑。
    """

    def __init__(self):
        self.user_repo = UserRepository()

    async def authenticate_user(
            self, db: AsyncSession, account_identifier: str, password: str
    ) -> Optional[User]:
        """
        用户登录验证逻辑 (支持 邮箱 OR 用户名 双重登录)。

        [架构优化] 多重身份解析
        用户的登录习惯各异。系统应具备智能识别能力，
        优先尝试将输入识别为邮箱，若失败则降级尝试识别为用户名。

        Args:
            account_identifier: 用户输入的账号 (可能是 email，也可能是 username)
            password: 明文密码
        """
        # 1. 尝试作为邮箱查询
        user = await self.user_repo.get_by_email(db, email=account_identifier)

        # 2. 如果没找到，尝试作为用户名查询
        if not user:
            user = await self.user_repo.get_by_username(db, username=account_identifier)

        # 3. 如果都不存在，返回 None (认证失败)
        if not user:
            return None

        # 4. 验证密码 (使用 Argon2)
        # 注意：verify_password 内部已封装了异常处理，这里直接判断 bool 即可
        if not verify_password(password, user.password_hash):
            return None

        return user

    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        用户注册业务逻辑。
        """
        # 1. 查重逻辑：邮箱
        if await self.user_repo.get_by_email(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        # 2. 查重逻辑：用户名
        if await self.user_repo.get_by_username(db, username=user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用",
            )

        # 3. 密码哈希与数据准备
        user_data = user_in.model_dump()
        hashed_password = get_password_hash(user_data.pop("password"))

        # 4. 构造实体并持久化
        # 直接使用 Model 构造器以绕过 Schema 的字段差异
        db_user = User(
            **user_data,
            password_hash=hashed_password
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    def create_token_for_user(self, user: User) -> Token:
        """
        为指定用户签发 Access Token。
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")


# 实例化单例
auth_service = AuthService()
