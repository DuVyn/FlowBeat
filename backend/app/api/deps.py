# [设计模式] 依赖注入 (DI) / 资源获取即初始化 (RAII) 的变体
# [设计意图]
# 1. 解耦: 业务逻辑函数只需声明需要 Session，无需关心 Session 如何创建。
# 2. 事务边界控制: 确保每个 HTTP 请求拥有独立的数据库会话，请求结束自动清理。
# =============================================================================

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 创建异步数据库引擎
# echo=True: 在控制台打印生成的 SQL，仅在开发调试阶段开启，生产环境应通过日志配置关闭。
# future=True: 启用 SQLAlchemy 2.0 风格的 API。
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,
    future=True
)

# 创建异步会话工厂
# [关键配置解析] expire_on_commit=False
# 为什么这么写:
# 在 SQLAlchemy 的异步模式中，属性的"延迟加载" (Lazy Loading) 是不支持的（因为需要隐式的 I/O 操作）。
# 如果设置为 True（默认值），commit 后对象属性会过期，再次访问时会尝试触发 I/O 从而报错。
# 设置为 False 确保对象在 commit 后依然在内存中保持可用状态。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    [依赖项] 获取数据库会话

    用法: 在 FastAPI 路由中通过 db: AsyncSession = Depends(get_db) 注入。
    原理: 使用 Python 生成器 (yield) 实现上下文管理。
    """
    async with AsyncSessionLocal() as session:
        try:
            # 将会话控制权移交给路由处理函数
            yield session
        except Exception:
            # 异常处理: 若业务逻辑抛出未捕获异常，强制回滚事务，防止脏数据污染数据库。
            await session.rollback()
            raise
        finally:
            # 资源清理: 无论成功与否，必须关闭会话，释放连接回连接池。
            await session.close()
