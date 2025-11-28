from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models.user import UserRole


# ==========================================
# 基础 Schema (共享属性)
# ==========================================
class UserBase(BaseModel):
    """
    用户基础模式，包含创建和读取时共有的字段。
    """
    email: EmailStr = Field(..., description="用户邮箱，需符合标准邮箱格式")
    username: str = Field(..., min_length=3, max_length=50, description="唯一用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="用户全名或昵称")
    is_active: bool = Field(True, description="账户是否启用")
    role: UserRole = Field(UserRole.USER, description="用户角色权限")


# ==========================================
# 写入 Schema (Create/Update)
# ==========================================
class UserCreate(UserBase):
    """
    用户注册/创建时的请求体。
    必须包含明文密码，用于后续哈希处理。
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="明文密码，长度需在 8-100 字符之间"
    )


class UserUpdate(BaseModel):
    """
    用户更新资料时的请求体。
    所有字段均为 Optional，允许仅更新部分字段 (PATCH 语义)。
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None

    # 注意：通常不建议在普通 Update 接口允许修改 role，这需要管理员权限
    # 此处包含是为了通用性，Service 层需做权限校验


# ==========================================
# 响应 Schema (Response)
# ==========================================
class UserResponse(UserBase):
    """
    返回给前端的用户信息。
    严禁包含 password 或 password_hash 字段。
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 配置：允许从 ORM 对象 (SQLAlchemy Model) 读取数据
    model_config = ConfigDict(from_attributes=True)
