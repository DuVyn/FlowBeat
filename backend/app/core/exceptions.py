"""
自定义异常模块

本模块定义了项目专用的异常类层次结构，用于:
1. 统一错误响应格式 (Unified Error Response)
2. 精确的错误分类 (Error Classification)
3. 简化错误处理逻辑 (Error Handling Simplification)

设计原则:
1. 继承标准 HTTPException: 确保 FastAPI 能正确捕获并转换为 HTTP 响应。
2. 语义化命名: 异常类名直接表达错误类型，提高代码可读性。
3. 合理的状态码: 遵循 HTTP 语义，使用最恰当的状态码。

使用方式:
    from app.core.exceptions import BusinessError, NotFoundError

    # 在 Service 层抛出
    if user_exists:
        raise BusinessError("该邮箱已被注册")

    # 在 Repository 层抛出
    if not resource:
        raise NotFoundError("用户")
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class FlowBeatException(HTTPException):
    """
    项目基础异常类

    为什么自定义基类:
    1. 统一异常结构: 所有项目异常都继承此类，便于全局异常处理器统一拦截。
    2. 扩展能力: 可以添加项目特有的属性 (如 error_code、trace_id 等)。
    3. 类型安全: 便于类型检查和 IDE 提示。

    所有自定义业务异常应继承此类，而非直接继承 HTTPException。
    """

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化异常

        Args:
            status_code: HTTP 状态码
            detail: 错误详情，会直接返回给前端
            headers: 额外的响应头 (如 WWW-Authenticate)
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthError(FlowBeatException):
    """
    认证失败异常

    适用场景:
    1. Token 过期或无效
    2. Token 签名不匹配
    3. 未携带 Authorization 头
    4. 用户凭证错误

    为什么使用 401 状态码:
    HTTP 401 Unauthorized 表示请求需要身份验证，客户端应提供有效凭证后重试。
    注意: 401 实际上是"未认证"而非"未授权"，权限不足应使用 403。

    为什么添加 WWW-Authenticate 头:
    这是 HTTP 规范要求的，用于告知客户端应使用何种认证方式 (如 Bearer Token)。
    """

    def __init__(self, detail: str = "认证失败，请重新登录") -> None:
        """
        初始化认证异常

        Args:
            detail: 错误描述，默认为通用提示以避免信息泄露
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class BusinessError(FlowBeatException):
    """
    业务逻辑冲突异常

    适用场景:
    1. 邮箱/用户名已被注册
    2. 资源状态不允许当前操作
    3. 业务规则校验失败
    4. 库存不足、余额不足等

    为什么使用 409 状态码:
    HTTP 409 Conflict 表示请求与当前资源状态冲突。
    相比 400 Bad Request，409 更精确地表达了"数据本身没问题，但业务规则不允许"的语义。

    与 400 的区别:
    - 400: 请求格式错误 (如 JSON 语法错误、必填字段缺失)
    - 409: 请求格式正确，但违反业务规则 (如邮箱已存在)
    """

    def __init__(self, detail: str) -> None:
        """
        初始化业务异常

        Args:
            detail: 具体的业务错误描述，应包含用户可理解的信息
        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class NotFoundError(FlowBeatException):
    """
    资源未找到异常

    适用场景:
    1. 根据 ID 查询资源不存在
    2. 文件或路径不存在
    3. 关联的外键资源不存在

    为什么使用 404 状态码:
    HTTP 404 Not Found 是资源不存在的标准响应。
    客户端收到此响应后应理解为请求的资源从未存在或已被删除。

    安全注意事项:
    对于敏感资源 (如其他用户的私有数据)，即使资源存在但无权访问，
    也应返回 404 而非 403，以避免泄露资源存在性信息。
    """

    def __init__(self, resource_name: str) -> None:
        """
        初始化资源未找到异常

        Args:
            resource_name: 资源名称，用于生成友好的错误消息
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} 不存在或已被删除",
        )
