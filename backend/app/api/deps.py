from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import settings as security_settings  # 确保配置加载
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload
from app.repositories.user_repository import UserRepository

# =============================================================================
# 第一部分：数据库基础设施 (Infrastructure - Database)
# [设计模式] 资源获取即初始化 (RAII)
# =============================================================================

# 创建异步数据库引擎
# echo=True: 开发模式下打印 SQL，便于调试 N+1 问题
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,
    future=True
)

# 创建异步会话工厂
# expire_on_commit=False: 关键配置！
# 解释: SQLAlchemy 异步模式不支持隐式 IO (Lazy Loading)。
# 若为 True，commit 后属性会过期，再次访问触发 IO 会报错。设为 False 确保对象在 commit 后保持内存可用。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    [依赖注入] 数据库会话生成器

    生命周期管理:
    1. 请求开始: 创建新 Session
    2. yield: 移交控制权给路由处理函数
    3. 请求结束/异常: 自动回滚或关闭，防止连接泄漏
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# 第二部分：安全与认证 (Security & Authentication)
# [设计模式] 依赖链 (Dependency Chaining) / 组合模式
# =============================================================================

# 定义 OAuth2 规范流程
# 这告诉 Swagger UI 去哪里获取 Token (/api/v1/auth/login)
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


async def get_current_user(
        db: Annotated[AsyncSession, Depends(get_db)],
        token: Annotated[str, Depends(reusable_oauth2)]
) -> User:
    """
    [依赖注入] 验证 Token 并获取当前用户实体

    逻辑链:
    1. Depends(reusable_oauth2): 从 Header 提取 Bearer Token
    2. jwt.decode: 验证签名有效性与过期时间
    3. Depends(get_db): 获取数据库连接
    4. UserRepository: 查询用户是否存在及状态是否正常

    异常处理:
    - 401 Unauthorized: Token 无效、过期或伪造
    - 400 Bad Request: 用户被禁用
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码 JWT
        # algorithms 参数必须显式指定，防止算法降级攻击 (Algorithm Downgrade Attack)
        payload = jwt.decode(
            token,
            security_settings.SECRET_KEY,
            algorithms=[security_settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if token_data.sub is None:
            raise credentials_exception

    except (JWTError, ValidationError):
        # 捕获所有 JWT 相关错误 (过期、格式错误、签名不匹配)
        raise credentials_exception

    # 使用仓储层查询用户
    # 既然 deps.py 已经有了 Session，这里直接实例化 Repo 并传入 db
    repo = UserRepository()
    user = await repo.get(db, id=token_data.sub)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已停用")

    return user


async def get_current_active_superuser(
        current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    [依赖注入] 权限守卫：仅限管理员

    原理: 基于 get_current_user 的结果进一步校验 role 字段
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要管理员权限"
        )
    return current_user
