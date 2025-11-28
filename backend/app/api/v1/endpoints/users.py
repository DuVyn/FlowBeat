from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.auth_service import auth_service
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.models.user import User
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/", response_model=UserResponse)
async def register_user(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        user_in: UserCreate,
) -> Any:
    """
    注册新用户

    [权限] 公开接口 (无需 Token)
    """
    # 注册逻辑包含复杂的查重和哈希，委托给 Service 层
    user = await auth_service.register_user(db, user_in=user_in)
    return user


@router.get("/me", response_model=UserResponse)
async def read_user_me(
        current_user: Annotated[User, Depends(deps.get_current_user)],
) -> Any:
    """
    获取当前登录用户的个人资料

    [权限] 需要有效的 Access Token
    [机制] 利用依赖注入直接获取已验证的用户对象，无需查库
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_me(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        user_update: UserUpdate,
        current_user: Annotated[User, Depends(deps.get_current_user)],
) -> Any:
    """
    更新当前用户的个人资料

    [逻辑]
    1. 接收部分字段 (PATCH 语义)。
    2. 调用 Repository 进行原子更新。
    3. 返回更新后的最新数据。
    """
    # 实例化仓储 (这里也可以用依赖注入，但直接实例化保持简单)
    repo = UserRepository()

    # 如果用户尝试修改敏感信息（如角色），应在这里拦截
    # 本示例暂不开放修改 role，UserUpdate Schema 中虽有定义但建议在 Service 层过滤
    # 为安全起见，我们手动排除 role 字段的更新，防止普通用户提权
    if user_update.role is not None:
        raise HTTPException(status_code=403, detail="禁止修改用户角色")

    # 执行更新
    # 之前的 BaseRepository.update 已经处理了 exclude_unset=True 逻辑
    updated_user = await repo.update(db, db_obj=current_user, obj_in=user_update)
    return updated_user
