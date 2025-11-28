"""
用户管理 API 端点

本模块提供用户相关的接口:
1. 用户注册 (POST /)
2. 获取当前用户信息 (GET /me)
3. 更新当前用户信息 (PATCH /me)

设计原则:
1. RESTful 风格: 使用标准 HTTP 方法表达操作语义。
2. 权限隔离: 普通用户只能操作自己的资源。
3. PATCH 语义: 更新接口支持部分字段更新。
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/", response_model=UserResponse)
async def register_user(
    *,
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    user_in: UserCreate,
) -> Any:
    """
    用户注册接口

    权限: 公开接口，无需 Token

    业务逻辑:
    1. 验证邮箱和用户名的唯一性
    2. 对密码进行 Argon2id 哈希处理
    3. 创建用户记录并返回

    请求体:
        {
            "email": "user@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "full_name": "张三"  // 可选
        }

    响应:
        UserResponse: 新创建的用户信息 (不含密码)

    异常:
        400: 邮箱或用户名已被注册

    Args:
        db: 数据库会话 (自动注入)
        user_in: 用户注册请求体 (自动验证)

    Returns:
        User: 新创建的用户实体
    """
    # 委托给 Service 层处理
    # Service 层负责: 查重、密码哈希、实体创建
    user = await auth_service.register_user(db, user_in=user_in)
    return user


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: Annotated[User, Depends(deps.get_current_user)],
) -> Any:
    """
    获取当前登录用户的个人资料

    权限: 需要有效的 Access Token

    设计优势:
    利用依赖注入直接获取已验证的用户对象，无需额外查库。
    get_current_user 依赖已经完成了:
    1. Token 验证
    2. 用户查询
    3. 状态检查

    响应:
        UserResponse: 当前用户的完整信息 (不含密码)

    Args:
        current_user: 当前登录用户 (自动注入)

    Returns:
        User: 当前用户实体
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

    权限: 需要有效的 Access Token

    支持的字段 (PATCH 语义，仅更新传入的字段):
    - email: 新邮箱地址
    - username: 新用户名
    - full_name: 新昵称
    - password: 新密码

    安全限制:
    1. 禁止普通用户修改 role 字段，防止提权攻击
    2. 禁止修改 is_active 字段，防止自我激活

    请求体示例:
        {
            "full_name": "李四"
        }

    响应:
        UserResponse: 更新后的用户信息

    异常:
        403: 尝试修改角色

    Args:
        db: 数据库会话 (自动注入)
        user_update: 更新请求体 (自动验证)
        current_user: 当前登录用户 (自动注入)

    Returns:
        User: 更新后的用户实体
    """
    # 实例化仓储
    repo = UserRepository()

    # 安全检查: 拒绝角色提权请求
    # 为什么在这里检查而非 Schema 层:
    # Schema 层负责数据结构定义，权限控制应在 API 层实现。
    # 这样管理员接口可以复用同一个 Schema 但允许修改角色。
    if user_update.role is not None:
        raise HTTPException(
            status_code=403,
            detail="禁止修改用户角色",
        )

    # 执行更新
    # BaseRepository.update 会自动处理 exclude_unset=True，
    # 只更新请求体中明确传入的字段
    updated_user = await repo.update(db, db_obj=current_user, obj_in=user_update)
    return updated_user
