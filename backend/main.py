from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 初始化 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="FlowBeat 音乐推荐系统后端 API - 基于 DDD 与 敏捷开发",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS (跨域资源共享)
# 安全性权衡：只允许白名单内的域名访问，防止恶意站点盗用 API。
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,  # 允许携带 Cookie/Token (JWT 认证必须)
        allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE...)
        allow_headers=["*"],  # 允许所有 Header (Authorization, Content-Type...)
    )


@app.get("/health")
async def health_check():
    """
    健康检查接口 (Health Check)

    作用：
    1. Docker Healthcheck 探针。
    2. K8s Liveness/Readiness 探针。
    3. 负载均衡器的心跳检测。
    """
    return {"status": "ok", "app_name": settings.PROJECT_NAME}

# TODO: 注册 API 路由 (将在后续阶段添加)
# app.include_router(api_router, prefix=settings.API_V1_STR)
