from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

# 定义泛型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用 CRUD 仓储基类

    [设计意图]
    封装基础的 CRUD 操作，通过泛型支持不同模型和 Schema 的自动推导。
    采用 Session-per-Method 策略，将 DB Session 的生命周期管理交由调用层（Service/API）控制。
    """

    def __init__(self, model: Type[ModelType]):
        """
        :param model: SQLAlchemy 模型类 (如 User)
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据主键查询单条记录
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        分页查询多条记录
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录

        [原理]
        使用 model_dump() 将 Pydantic 对象转换为字典，保留 Python 原生类型（如 datetime），
        交由 SQLAlchemy 处理 SQL 转义。
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
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新现有记录 (支持 PATCH 语义)
        """
        # 1. 获取现有对象的数据字典
        # 使用 __dict__ 通常包含 SQLA 的内部状态，pydantic 的 from_attributes 更安全，
        # 但此处我们需要的是这一行数据的原始值用于对比，或者简单的 setattr 覆盖。
        # 直接遍历更新字段是最稳健的方式。

        # 2. 解析更新数据
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True 确保只更新前端显式传递的字段
            update_data = obj_in.model_dump(exclude_unset=True)

        # 3. 映射修改
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        # 4. 持久化
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
