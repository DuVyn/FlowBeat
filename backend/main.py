"""
FlowBeat 后端主入口模块

本模块是 FastAPI 应用的入口点，负责:
1. 应用实例的创建和配置
2. 中间件的注册 (CORS)
3. 路由的挂载
4. 全局异常处理器的定义
5. 运维探针端点的提供

启动方式:
    # 开发环境
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

    # 生产环境
    uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings


# =============================================================================
# 应用工厂函数
# =============================================================================
def create_application() -> FastAPI:
    """
    FastAPI 应用工厂函数

    为什么使用工厂模式:
    虽然对于单例应用不是严格必须，但封装为工厂函数有以下优势:
    1. 单元测试隔离: 每个测试可以创建独立的应用实例
    2. 环境配置: 不同环境 (Dev/Prod) 可以注入不同的启动配置
    3. 延迟初始化: 应用创建时机可控，便于集成测试

    Returns:
        FastAPI: 配置完成的应用实例
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        description="FlowBeat 音乐推荐系统后端 API - 基于 DDD 与敏捷开发",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # =========================================================================
    # 中间件配置 (Middleware)
    # =========================================================================

    # 配置 CORS (跨域资源共享)
    #
    # 为什么需要 CORS:
    # 浏览器的同源策略会阻止前端 JavaScript 访问不同源的 API。
    # CORS 是一种 HTTP 机制，允许服务器声明哪些源可以访问其资源。
    #
    # 安全考量:
    # - allow_credentials=True: 必须开启，否则前端无法发送携带 JWT 的请求头
    # - allow_origins: 严格限制为 .env 中配置的白名单，防止 CSRF 攻击
    # - 生产环境绝不使用通配符 "*"
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],  # 允许所有 HTTP 方法
            allow_headers=["*"],  # 允许所有请求头
        )

    # =========================================================================
    # 路由注册 (Router Registration)
    # =========================================================================

    # 挂载 API V1 路由树
    # 所有子模块 (Auth, Users) 的路由都通过 api_router 统一接入
    # prefix: 为所有接口添加统一版本前缀 (如 /api/v1)
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


# =============================================================================
# 应用实例化
# =============================================================================
# 模块级应用实例，uvicorn 通过 main:app 引用此变量
app = create_application()


# =============================================================================
# 运维探针 (Operational Probes)
# =============================================================================
@app.get("/health", tags=["system"])
async def health_check():
    """
    健康检查接口

    用途:
    1. Docker Healthcheck: 容器健康状态检测
    2. Kubernetes Liveness Probe: K8s 存活探针
    3. 负载均衡器心跳: Nginx/AWS ALB 的后端健康检查
    4. 运维监控: 快速验证服务连通性

    设计原则:
    1. 轻量级: 不执行数据库查询等耗时操作
    2. 快速响应: 避免因数据库压力导致健康检查超时
    3. 信息最小化: 只返回必要信息，不暴露内部细节

    Returns:
        dict: 包含状态和应用名称
    """
    return {"status": "ok", "app_name": settings.PROJECT_NAME}


# =============================================================================
# 全局异常处理 (Global Exception Handlers)
# =============================================================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP 异常统一处理器

    为什么需要自定义处理器:
    确保所有 HTTP 异常都返回一致的 JSON 格式，便于前端统一处理。

    Args:
        request: 请求对象 (未使用，但是框架要求的签名)
        exc: HTTPException 实例

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    请求参数校验异常处理器

    触发时机:
    当 Pydantic 模型校验失败时触发，例如:
    - 必填字段缺失
    - 字段类型不匹配
    - 字段值不满足约束条件

    响应设计:
    返回详细的字段错误信息，包含:
    - loc: 错误字段的位置 (如 ["body", "email"])
    - msg: 错误描述
    - type: 错误类型

    Args:
        request: 请求对象 (未使用)
        exc: RequestValidationError 实例

    Returns:
        JSONResponse: 422 状态码和详细的验证错误信息
    """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
