"""
认证服务模块

本模块提供用户认证相关的业务逻辑:
1. authenticate_user - 用户登录验证
2. register_user - 用户注册
3. create_token_for_user - Token 签发

设计原则:
1. 领域服务: 封装跨实体的业务逻辑，协调仓储和安全模块
2. 单一职责: 只处理认证相关的业务规则
3. 无状态: 服务本身不持有状态，便于水平扩展

使用方式:
    from app.services.auth_service import auth_service

    # 用户登录
    user = await auth_service.authenticate_user(db, "user@example.com", "password")

    # 签发 Token
    token = auth_service.create_token_for_user(user)
"""

from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate


class AuthService:
    """
    认证领域服务 (Domain Service)

    为什么使用服务类而非纯函数:
    1. 依赖管理: 可以在构造时注入依赖 (如仓储)
    2. 可测试性: 便于 mock 依赖进行单元测试
    3. 逻辑聚合: 相关的业务方法组织在一起

    职责边界:
    - 处理登录验证逻辑
    - 处理用户注册逻辑
    - 协调密码哈希和 Token 签发
    - 不直接操作数据库，通过仓储层访问数据
    """

    def __init__(self) -> None:
        """
        初始化认证服务

        为什么在构造时创建仓储:
        遵循依赖注入原则，仓储作为服务的依赖在构造时注入。
        这样便于在测试时替换为 mock 仓储。
        """
        self.user_repo = UserRepository()

    async def authenticate_user(
        self,
        db: AsyncSession,
        account_identifier: str,
        password: str,
    ) -> Optional[User]:
        """
        用户登录验证 (支持邮箱或用户名双重登录)

        业务规则:
        1. 尝试将输入识别为邮箱进行查询
        2. 若邮箱未找到，尝试作为用户名查询
        3. 验证密码哈希是否匹配
        4. 返回用户实体或 None

        安全设计:
        1. 无论是用户不存在还是密码错误，都返回 None
           这样调用方无法区分具体失败原因，防止用户枚举攻击
        2. 密码验证使用恒定时间比较，防止时序攻击

        为什么支持双重登录:
        用户的登录习惯各异，有人习惯用邮箱，有人习惯用用户名。
        提供灵活的登录方式可以提升用户体验，减少登录失败率。

        Args:
            db: 数据库会话
            account_identifier: 账号标识 (邮箱或用户名)
            password: 明文密码

        Returns:
            Optional[User]: 验证成功返回用户实体，失败返回 None
        """
        # 1. 尝试作为邮箱查询
        user = await self.user_repo.get_by_email(db, email=account_identifier)

        # 2. 如果邮箱未找到，尝试作为用户名查询
        if not user:
            user = await self.user_repo.get_by_username(db, username=account_identifier)

        # 3. 用户不存在
        if not user:
            return None

        # 4. 验证密码
        # verify_password 内部已封装异常处理，直接判断 bool 即可
        if not verify_password(password, user.password_hash):
            return None

        return user

    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        用户注册业务逻辑

        业务规则:
        1. 邮箱必须唯一
        2. 用户名必须唯一
        3. 密码必须经过哈希处理后存储
        4. 新用户默认为普通用户角色

        事务处理:
        整个注册过程在单个事务中完成，确保原子性。
        如果任何步骤失败，所有更改都会回滚。

        为什么不使用仓储的 create 方法:
        1. 需要先进行查重逻辑
        2. 需要对密码进行哈希处理
        3. 请求 Schema (UserCreate) 和实体结构不完全匹配

        Args:
            db: 数据库会话
            user_in: 用户注册请求数据

        Returns:
            User: 新创建的用户实体

        Raises:
            HTTPException: 400 - 邮箱或用户名已被注册
        """
        # 1. 查重逻辑: 邮箱
        if await self.user_repo.get_by_email(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        # 2. 查重逻辑: 用户名
        if await self.user_repo.get_by_username(db, username=user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用",
            )

        # 3. 密码哈希与数据准备
        # 从 Schema 获取字典，弹出明文密码，添加哈希密码
        user_data = user_in.model_dump()
        hashed_password = get_password_hash(user_data.pop("password"))

        # 4. 构造实体并持久化
        # 直接使用 Model 构造器，因为 Schema 字段名与实体不完全匹配
        # (Schema 中是 password，实体中是 password_hash)
        db_user = User(
            **user_data,
            password_hash=hashed_password,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    def create_token_for_user(self, user: User) -> Token:
        """
        为指定用户签发 Access Token

        设计说明:
        1. Token 中只存储用户 ID，不存储其他信息
        2. 过期时间从全局配置读取
        3. 返回符合 OAuth2 规范的 Token 对象

        为什么是同步方法:
        Token 签发是纯 CPU 计算操作 (JWT 编码)，不涉及 IO，
        使用同步方法即可，无需 async。

        Args:
            user: 已验证的用户实体

        Returns:
            Token: 包含 access_token 和 token_type 的响应对象
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id,
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")


# =============================================================================
# 单例实例化
# =============================================================================
# 为什么使用模块级单例:
# 1. 服务本身无状态，多个请求可以共享同一实例
# 2. 避免每次请求都创建新的服务实例，减少内存分配
# 3. 仓储层的 Session 是外部传入的，不影响线程安全
auth_service = AuthService()
