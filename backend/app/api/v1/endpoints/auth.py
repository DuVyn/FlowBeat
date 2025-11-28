"""
认证相关 API 端点

本模块提供用户认证相关的接口:
1. 登录获取 Token (/login/access-token)

设计原则:
1. OAuth2 兼容: 遵循 OAuth2 密码模式规范，便于第三方集成。
2. 双重登录: 支持邮箱或用户名登录，提升用户体验。
3. 安全响应: 错误信息不暴露具体失败原因，防止用户枚举攻击。
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.token import Token
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: Annotated[AsyncSession, Depends(deps.get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Any:
    """
    OAuth2 兼容的 Token 登录接口

    接口设计:
    1. 使用 OAuth2PasswordRequestForm 接收表单数据，符合 OAuth2 规范。
    2. 支持邮箱或用户名登录，form_data.username 字段可接收两种格式。
    3. 验证成功后签发 JWT Access Token。

    请求格式 (application/x-www-form-urlencoded):
        username: 邮箱或用户名
        password: 明文密码

    响应格式:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }

    安全注意事项:
    1. 登录失败统一返回"账号或密码错误"，不区分"用户不存在"和"密码错误"。
    2. 用户被禁用返回不同的错误信息，便于客户端引导用户联系管理员。

    Args:
        db: 数据库会话 (自动注入)
        form_data: OAuth2 表单数据 (自动注入)

    Returns:
        Token: 包含 access_token 和 token_type

    Raises:
        HTTPException: 401 - 账号或密码错误
        HTTPException: 400 - 用户账户已停用
    """
    # 验证用户凭证
    # form_data.username 包含用户输入的账号字符串 (可能是邮箱或用户名)
    # Service 层会自动识别并尝试两种查询方式
    user = await auth_service.authenticate_user(
        db,
        account_identifier=form_data.username,
        password=form_data.password,
    )

    # 认证失败: 用户不存在或密码错误
    # 为什么返回 401: HTTP 401 Unauthorized 是登录失败的标准状态码
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 账户被禁用
    # 为什么返回 400 而非 401: 用户凭证正确但账户状态异常，属于业务限制
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="用户账户已停用",
        )

    # 签发 Token 并返回
    return auth_service.create_token_for_user(user)
