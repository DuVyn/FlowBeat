"""
用户数据传输对象模块 (User DTOs / Schemas)

本模块定义了用户相关的 Pydantic 模型，用于:
1. 请求体验证 (Request Body Validation)
2. 响应体序列化 (Response Serialization)
3. API 文档自动生成 (OpenAPI Schema Generation)

设计原则:
1. 职责分离: 不同场景使用不同的 Schema，避免字段泄露。
2. 严格验证: 利用 Pydantic 的类型系统和验证器确保数据合法性。
3. 文档友好: 每个字段都包含 description，便于生成清晰的 API 文档。

安全注意事项:
- UserCreate 包含明文密码，仅用于接收前端输入，Service 层必须立即哈希处理。
- UserResponse 严禁包含 password 或 password_hash 字段，防止敏感信息泄露。
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


# =============================================================================
# 基础 Schema (共享属性)
# =============================================================================
class UserBase(BaseModel):
    """
    用户基础模式

    为什么抽取基类:
    遵循 DRY (Don't Repeat Yourself) 原则，将创建和读取场景共有的字段抽取到基类，
    减少代码重复，保证字段定义的一致性。

    字段设计说明:
    - email: 使用 EmailStr 类型，Pydantic 会自动进行 RFC 5322 格式校验。
    - username: 限制长度为 3-50 字符，避免过短或过长的用户名。
    - full_name: 可选字段，降低注册门槛。
    - is_active: 默认为 True，新注册用户默认激活。
    - role: 默认为普通用户，遵循最小权限原则。
    """

    email: EmailStr = Field(
        ...,
        description="用户邮箱，需符合标准邮箱格式",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="唯一用户名，3-50 个字符",
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="用户全名或昵称，可选",
    )
    is_active: bool = Field(
        True,
        description="账户是否启用",
    )
    role: UserRole = Field(
        UserRole.USER,
        description="用户角色权限",
    )


# =============================================================================
# 写入 Schema (Create/Update)
# =============================================================================
class UserCreate(UserBase):
    """
    用户注册请求体

    为什么继承 UserBase:
    注册时需要填写所有基础信息，同时额外需要密码字段。
    继承可以复用基类的字段定义和验证规则。

    密码字段设计:
    - 最小 8 字符: 符合 NIST 密码安全建议的最低要求。
    - 最大 100 字符: 防止超长密码导致的 DoS 攻击 (哈希计算耗时过长)。
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="明文密码，长度需在 8-100 字符之间",
    )


class UserUpdate(BaseModel):
    """
    用户资料更新请求体

    为什么不继承 UserBase:
    更新场景采用 PATCH 语义，所有字段均为可选。
    若继承 UserBase，则 email 和 username 会变成必填，不符合部分更新的需求。

    为什么包含 role 字段:
    虽然普通用户不应修改自己的角色，但 Schema 层仅负责数据结构定义。
    权限控制应在 API 层 (Endpoint) 或 Service 层实现，这里保留字段以支持管理员操作。
    API 层会检查此字段并拒绝普通用户的提权请求。
    """

    email: Optional[EmailStr] = Field(
        None,
        description="新邮箱地址",
    )
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="新用户名",
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="新的全名或昵称",
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="新密码",
    )
    is_active: Optional[bool] = Field(
        None,
        description="账户启用状态",
    )
    role: Optional[UserRole] = Field(
        None,
        description="用户角色，普通用户无权修改此字段",
    )


# =============================================================================
# 响应 Schema (Response)
# =============================================================================
class UserResponse(UserBase):
    """
    用户信息响应体

    为什么继承 UserBase:
    响应需要返回用户的所有基础信息，同时附加系统生成的字段 (id, 时间戳)。

    安全设计:
    此 Schema 明确排除了 password 和 password_hash 字段。
    即使 ORM 对象包含这些字段，Pydantic 的 from_attributes 模式也只会提取 Schema 中定义的字段，
    从根本上防止敏感信息泄露。
    """

    id: UUID = Field(
        ...,
        description="用户唯一标识符",
    )
    created_at: datetime = Field(
        ...,
        description="账户创建时间",
    )
    updated_at: datetime = Field(
        ...,
        description="最后更新时间",
    )

    # Pydantic v2 配置
    # from_attributes=True: 允许从 ORM 对象 (SQLAlchemy Model) 直接读取数据
    # 这是 Pydantic v1 中 orm_mode=True 的替代配置
    model_config = ConfigDict(from_attributes=True)
