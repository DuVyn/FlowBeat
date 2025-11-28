"""
通用 CRUD 仓储基类模块

本模块提供泛型仓储基类，封装常见的数据库 CRUD 操作:
1. get - 根据主键查询单条记录
2. get_multi - 分页查询多条记录
3. create - 创建新记录
4. update - 更新现有记录
5. remove - 删除记录

设计原则:
1. 泛型支持: 通过 TypeVar 支持不同模型和 Schema 的类型推导
2. Session 外置: 将 Session 的生命周期管理交由调用层控制
3. 异常透传: 数据库异常直接抛出，由上层统一处理

使用方式:
    class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
        def __init__(self):
            super().__init__(User)
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

# =============================================================================
# 泛型类型变量定义
# =============================================================================
# ModelType: SQLAlchemy 模型类型，必须继承自 Base
# CreateSchemaType: 创建时使用的 Pydantic Schema
# UpdateSchemaType: 更新时使用的 Pydantic Schema
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用 CRUD 仓储基类

    为什么使用仓储模式:
    1. 解耦业务逻辑与数据访问: Service 层无需关心具体的 SQL 查询
    2. 统一数据访问接口: 所有实体使用相同的 CRUD 方法签名
    3. 便于测试: 可以轻松 mock 仓储层进行单元测试
    4. 便于切换存储: 未来如需更换数据库，只需修改仓储实现

    泛型参数说明:
    - ModelType: 数据库实体类型 (如 User)
    - CreateSchemaType: 创建操作的请求 Schema (如 UserCreate)
    - UpdateSchemaType: 更新操作的请求 Schema (如 UserUpdate)
    """

    def __init__(self, model: Type[ModelType]) -> None:
        """
        初始化仓储

        为什么需要传入 model:
        Python 泛型在运行时会被擦除，无法直接获取泛型参数的具体类型。
        因此需要在构造时显式传入模型类，用于构建 SQL 查询。

        Args:
            model: SQLAlchemy 模型类 (如 User)
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据主键查询单条记录

        为什么返回 Optional:
        当记录不存在时返回 None，调用方需要处理这种情况。
        这比抛出异常更符合查询语义 - 查询本身是成功的，只是没有结果。

        Args:
            db: 数据库会话
            id: 主键值

        Returns:
            Optional[ModelType]: 找到则返回实体，否则返回 None
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        分页查询多条记录

        为什么使用关键字参数:
        强制调用方使用命名参数 (skip=0, limit=10)，提高代码可读性。
        避免 get_multi(db, 0, 10) 这种含义不清的调用。

        为什么默认 limit=100:
        防止一次性加载过多数据导致内存溢出。
        调用方可以根据需求调整，但默认值提供了安全边界。

        Args:
            db: 数据库会话
            skip: 跳过的记录数 (用于分页偏移)
            limit: 返回的最大记录数

        Returns:
            List[ModelType]: 实体列表，可能为空
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录

        事务处理:
        1. 将实体添加到 Session
        2. 执行 commit 持久化
        3. 刷新实体以获取数据库生成的值 (如 ID、默认时间戳)
        4. 异常时自动回滚

        为什么使用 model_dump:
        Pydantic v2 推荐使用 model_dump() 替代 dict()。
        此方法会保留 Python 原生类型，交由 SQLAlchemy 处理 SQL 转义。

        Args:
            db: 数据库会话
            obj_in: 创建请求的 Schema 对象

        Returns:
            ModelType: 创建并持久化后的实体

        Raises:
            Exception: 数据库异常 (如唯一约束冲突)
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
        except Exception:
            await db.rollback()
            raise
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        更新现有记录 (支持 PATCH 语义)

        PATCH vs PUT:
        - PUT: 完整替换，所有字段都必须提供
        - PATCH: 部分更新，只更新提供的字段

        本方法支持 PATCH 语义，通过 exclude_unset=True 只更新请求中明确设置的字段。

        为什么支持 Dict 和 Schema 两种输入:
        1. Schema: 标准用法，来自 API 请求体
        2. Dict: 内部调用时更灵活，无需构造 Schema 对象

        Args:
            db: 数据库会话
            db_obj: 待更新的数据库实体
            obj_in: 更新数据 (Schema 或字典)

        Returns:
            ModelType: 更新后的实体

        Raises:
            Exception: 数据库异常
        """
        # 解析更新数据
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True: 只包含请求中显式设置的字段
            # 这是实现 PATCH 语义的关键
            update_data = obj_in.model_dump(exclude_unset=True)

        # 映射修改到实体
        # 为什么使用 hasattr 检查: 防止字典中包含模型不存在的字段导致 AttributeError
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        # 持久化更新
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
        except Exception:
            await db.rollback()
            raise
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        根据主键删除记录

        设计说明:
        1. 先查询再删除: 返回被删除的实体，便于日志记录或返回给调用方
        2. 不存在时返回 None: 调用方可以据此决定是否抛出 404 异常

        物理删除 vs 软删除:
        本方法执行物理删除。如需软删除，应使用 update 方法设置 is_active=False。

        Args:
            db: 数据库会话
            id: 主键值

        Returns:
            Optional[ModelType]: 被删除的实体，不存在则返回 None

        Raises:
            Exception: 数据库异常
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise
        return obj
