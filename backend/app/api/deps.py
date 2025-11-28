"""
FastAPI 依赖注入模块

本模块提供应用核心的依赖项 (Dependencies)，用于:
1. 数据库会话管理 (Database Session Management)
2. 用户认证与授权 (Authentication & Authorization)
3. 权限校验 (Permission Checking)

设计原则:
1. 依赖链: 复杂的依赖通过组合简单依赖实现，如 get_current_user 依赖 get_db。
2. 关注点分离: 每个依赖函数只负责一个职责。
3. 可测试性: 依赖可以在测试中被轻松替换 (Override)。

使用方式:
    from fastapi import Depends
    from app.api import deps

    @router.get("/protected")
    async def protected_route(
        current_user: User = Depends(deps.get_current_user)
    ):
        return {"user": current_user.username}
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import settings as security_settings
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.token import TokenPayload

# =============================================================================
# 第一部分: 数据库基础设施 (Infrastructure - Database)
# =============================================================================

# 创建异步数据库引擎
#
# 为什么使用 create_async_engine:
# SQLAlchemy 2.0 原生支持异步操作，配合 asyncpg 驱动可以实现全链路异步。
# 相比同步模式，异步模式在高并发场景下可以显著提升吞吐量。
#
# echo=True 的作用:
# 开发模式下打印所有 SQL 语句，便于调试 N+1 查询问题。
# 生产环境应设置为 False 以避免日志膨胀。
#
# future=True 的作用:
# 启用 SQLAlchemy 2.0 风格的 API，确保使用最新的查询语法。
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,
    future=True,
)

# 创建异步会话工厂
#
# 为什么使用工厂模式:
# 每个请求需要独立的数据库会话，工厂模式可以按需创建新会话。
#
# expire_on_commit=False 的重要性:
# 这是异步 SQLAlchemy 的关键配置！
# 原理: SQLAlchemy 异步模式不支持隐式 IO (Lazy Loading)。
# 若为 True，commit 后对象属性会过期，再次访问会触发 IO 操作并报错。
# 设为 False 确保对象在 commit 后仍然可用，避免 "greenlet_spawn" 异常。
#
# autoflush=False 的作用:
# 禁用自动刷新，避免在查询前意外触发 flush 操作。
# 我们在需要时显式调用 commit，保持对事务的完全控制。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入生成器

    生命周期管理:
    1. 请求开始: 创建新的 AsyncSession
    2. yield: 移交控制权给路由处理函数
    3. 请求结束/异常: 自动回滚或关闭，防止连接泄漏

    为什么使用生成器:
    生成器模式允许在请求结束后执行清理逻辑 (finally 块)，
    确保数据库连接被正确释放回连接池。

    异常处理策略:
    - 捕获所有异常并回滚事务，防止脏数据
    - 重新抛出异常，让上层处理器记录和响应
    - finally 块确保连接一定被关闭

    Yields:
        AsyncSession: 数据库会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # 发生异常时回滚事务，防止部分写入
            await session.rollback()
            raise
        finally:
            # 确保会话被关闭，连接返回池中
            await session.close()


# =============================================================================
# 第二部分: 安全与认证 (Security & Authentication)
# =============================================================================

# OAuth2 密码模式配置
#
# 为什么使用 OAuth2PasswordBearer:
# 这是 FastAPI 提供的标准 OAuth2 密码模式实现。
# 它会从请求头中提取 "Authorization: Bearer <token>" 并返回 token 字符串。
#
# tokenUrl 的作用:
# 告诉 Swagger UI 在哪里获取 Token，使文档可以直接测试认证接口。
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(reusable_oauth2)],
) -> User:
    """
    验证 Token 并获取当前用户

    依赖链:
    1. Depends(reusable_oauth2): 从 Authorization 头提取 Bearer Token
    2. jwt.decode: 验证签名有效性与过期时间
    3. Depends(get_db): 获取数据库连接
    4. UserRepository: 查询用户是否存在及状态

    安全设计:
    1. algorithms 参数必须显式指定，防止算法降级攻击 (Algorithm Downgrade Attack)
    2. 所有 JWT 异常统一返回 401，不泄露具体失败原因
    3. 用户存在性和活跃状态分开检查，便于日志审计

    Args:
        db: 数据库会话 (自动注入)
        token: JWT Token 字符串 (自动从请求头提取)

    Returns:
        User: 已验证的用户实体

    Raises:
        HTTPException: 401 - Token 无效、过期或伪造
        HTTPException: 400 - 用户账户已被禁用
    """
    # 定义统一的认证异常
    # 为什么不使用 AuthError: 保持与 FastAPI 文档示例一致，便于维护
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码并验证 JWT
        # algorithms 必须显式指定: 防止攻击者将 Token 头部的 alg 改为 none
        payload = jwt.decode(
            token,
            security_settings.SECRET_KEY,
            algorithms=[security_settings.ALGORITHM],
        )
        # 解析载荷为强类型对象
        token_data = TokenPayload(**payload)

        # 检查 sub 字段是否存在
        if token_data.sub is None:
            raise credentials_exception

    except (JWTError, ValidationError):
        # 统一处理所有 JWT 相关错误
        # 包括: 签名不匹配、Token 过期、格式错误等
        # 为什么不区分具体错误: 防止攻击者通过错误信息推断 Token 结构
        raise credentials_exception

    # 查询用户实体
    repo = UserRepository()
    user = await repo.get(db, id=token_data.sub)

    # 用户不存在 (可能已被删除)
    if not user:
        raise credentials_exception

    # 用户已被禁用
    # 为什么返回 400 而非 401: 认证成功但账户状态异常，属于业务限制而非认证失败
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已停用")

    return user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    权限守卫: 仅限管理员访问

    设计原理:
    基于 get_current_user 的结果进一步校验 role 字段。
    这是"依赖链"模式的典型应用: 复杂权限由简单权限组合而成。

    使用场景:
    - 用户管理接口 (删除用户、修改角色等)
    - 系统配置接口
    - 数据导出接口

    Args:
        current_user: 已通过认证的用户 (自动注入)

    Returns:
        User: 已验证的管理员用户

    Raises:
        HTTPException: 403 - 用户不是管理员
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return current_user
