"""
JWT Token 相关 Schema 模块

本模块定义了 JWT Token 相关的数据传输对象:
1. Token - Token 响应模型
2. TokenPayload - Token 载荷模型

设计原则:
1. 符合 OAuth2 规范: Token 响应格式遵循 OAuth2 标准
2. 载荷最小化: 只存储必要信息，减少 Token 体积
3. 类型安全: 使用 Pydantic 进行载荷验证
"""

from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT Token 响应模型

    为什么这样设计:
    此结构符合 OAuth2 规范的标准响应格式，确保与各类 OAuth2 客户端库兼容。
    前端收到响应后，应将 access_token 存储在安全位置，
    并在后续请求头中携带 "Authorization: Bearer <token>"。

    字段说明:
    - access_token: JWT 字符串，包含用户身份和过期时间
    - token_type: 固定为 "bearer"，符合 OAuth2 Bearer Token 规范

    使用示例 (前端):
        const response = await fetch('/api/v1/auth/login/access-token', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        localStorage.setItem('token', data.access_token);

        // 后续请求
        fetch('/api/v1/users/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
    """

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    JWT 载荷模型

    为什么需要此模型:
    用于解析 JWT 解码后的载荷数据，提供类型安全的访问方式。
    Pydantic 会自动验证载荷结构，确保必要字段存在。

    字段说明:
    - sub (subject): 令牌主体，存储用户 ID
      为什么使用 str: UUID 在 JWT 中以字符串形式存储，解析后需要转换

    为什么载荷这么简单:
    1. 减小 Token 体积: 每个请求都携带 Token，体积过大影响性能
    2. 信息最小化原则: Token 可能被截获，不应包含敏感信息
    3. 实时性: 角色等信息应从数据库实时查询，确保权限变更立即生效

    注意事项:
    - exp (过期时间) 由 jwt 库自动处理，无需在此模型中定义
    - 如需扩展载荷，应仔细评估安全影响
    """

    sub: str | None = None
