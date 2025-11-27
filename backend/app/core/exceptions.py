from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class FlowBeatException(HTTPException):
    """
    项目基础异常类，所有自定义异常应继承此类。
    设计意图：统一异常结构，便于前端拦截器统一处理错误提示。
    """

    def __init__(
            self,
            status_code: int,
            detail: Any = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthError(FlowBeatException):
    """
    认证失败异常。
    场景：Token 过期、Token 无效、未携带 Token。
    """

    def __init__(self, detail: str = "认证失败，请重新登录"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class BusinessError(FlowBeatException):
    """
    业务逻辑冲突异常。
    场景：用户已存在、余额不足、前置条件不满足。
    使用 409 Conflict 状态码而非 400，以区分参数格式错误和业务逻辑冲突。
    """

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class NotFoundError(FlowBeatException):
    """
    资源未找到异常。
    场景：ID 不存在、文件不存在。
    """

    def __init__(self, resource_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} 不存在或已被删除"
        )
