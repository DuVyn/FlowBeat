"""
API V1 路由聚合模块

本模块将 V1 版本的所有子路由聚合到统一的路由器中。
这种设计遵循了关注点分离原则，每个功能模块有独立的路由文件。

路由结构:
    /api/v1/auth/...      - 认证相关接口
    /api/v1/users/...     - 用户管理接口

"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, music, users

# 创建 V1 版本的主路由器
api_router = APIRouter()

# =============================================================================
# 路由注册
# =============================================================================

# 认证路由
# 挂载点: /api/v1/auth/...
# 包含: 登录、Token 刷新等
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)

# 用户路由
# 挂载点: /api/v1/users/...
# 包含: 注册、获取/更新个人信息等
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

# 音乐资源路由
api_router.include_router(
    music.router,
    prefix="/music",
    tags=["music"],
)
