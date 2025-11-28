from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router


# =============================================================================
# [核心入口] 应用工厂与全局配置
# =============================================================================

def create_application() -> FastAPI:
    """
    FastAPI 应用工厂函数

    [设计模式] 工厂模式 (Factory Pattern)
    虽然对于单例应用不是严格必须，但封装为工厂函数有利于：
    1. 单元测试时的应用实例隔离。
    2. 方便在不同环境（Dev/Prod）注入不同的启动配置。
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        description="FlowBeat 音乐推荐系统后端 API - 基于 DDD 与 敏捷开发",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # =========================================================================
    # 中间件配置 (Middleware)
    # =========================================================================

    # 配置 CORS (跨域资源共享)
    # [安全权衡]
    # allow_credentials=True: 必须开启，否则前端无法发送携带 JWT 的 Authorization 头或 Cookie。
    # allow_origins: 严格限制为 .env 中配置的白名单，防止 CSRF 和恶意调用。
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE, PATCH)
            allow_headers=["*"],  # 允许所有 Header (Authorization, Content-Type 等)
        )

    # =========================================================================
    # 路由注册 (Router Registration)
    # =========================================================================

    # 挂载 API V1 路由树
    # 所有子模块 (Auth, Users) 的路由都通过 api_router 统一接入
    # prefix: 为所有接口添加统一版本前缀 (如 /api/v1)
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()


# =============================================================================
# 运维探针 (Operational Probes)
# =============================================================================

@app.get("/health", tags=["system"])
async def health_check():
    """
    健康检查接口 (Health Check)

    [作用]
    1. Docker Healthcheck / K8s Liveness Probe 的探测端点。
    2. 负载均衡器 (Nginx/AWS ALB) 的心跳检测。
    3. 简单的连通性测试。

    [注意] 此接口不应包含复杂的数据库查询，以免数据库压力导致服务被误判为不健康。
    """
    return {"status": "ok", "app_name": settings.PROJECT_NAME}


# =============================================================================
# 全局异常处理 (Global Exception Handlers)
# =============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    统一 HTTP 异常响应格式
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    统一参数校验异常响应格式 (Pydantic 校验失败时触发)

    [设计意图]
    默认的 422 错误信息结构较为复杂，此处可根据前端需求进行简化。
    目前保持默认行为，返回详细的字段错误信息以辅助调试。
    """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
