from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.auth_service import auth_service
from app.schemas.token import Token

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Any:
    """
    OAuth2 兼容的 Token 登录接口

    [架构修正]
    OAuth2 标准表单只有 `username` 和 `password` 两个字段。
    我们将 `username` 字段的值传递给 Service 层的 `account_identifier` 参数，
    从而支持 "邮箱 OR 用户名" 的双重登录逻辑。
    """
    # [关键修改] 参数名从 email 变更为 account_identifier
    # form_data.username: 包含了用户输入的账号字符串 (可能是邮箱，也可能是用户名)
    user = await auth_service.authenticate_user(
        db,
        account_identifier=form_data.username,
        password=form_data.password
    )

    if not user:
        # 401 Unauthorized 是登录失败的标准状态码
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已停用")

    # 签发 Token
    return auth_service.create_token_for_user(user)
