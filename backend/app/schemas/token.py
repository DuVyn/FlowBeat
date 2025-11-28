from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT Token 响应模型

    [设计意图]
    符合 OAuth2 规范的标准响应结构。
    前端会将 access_token 存储在 LocalStorage 或 Cookie 中，
    并在后续请求头中携带 "Authorization: Bearer <token>"。
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    JWT 载荷模型

    [设计意图]
    用于解析 Token 后存储核心业务数据 (如 sub/user_id)。
    保持载荷轻量，避免存入过多非敏感信息，减少带宽消耗。
    """
    sub: str | None = None
