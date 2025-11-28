from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

api_router = APIRouter()

# 注册认证路由: /api/v1/auth/login/access-token
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 注册用户路由: /api/v1/users/
api_router.include_router(users.router, prefix="/users", tags=["users"])
