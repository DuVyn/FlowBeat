# [设计模式] 仓储模式 (Repository Pattern) + 泛型 (Generics)
# [设计意图]
# 1. 关注点分离: 将数据访问细节 (SQL/ORM) 与业务逻辑 (Service) 彻底解耦。
# 2. 代码复用 (DRY): 封装 90% 的标准 CRUD 操作，避免为每个实体重复编写相同的 SQL。
# 3. 异步支持: 全程使用 SQLAlchemy 异步 API (await db.execute)。
# =============================================================================

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

# 定义泛型变量，对传入的类型进行约束
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        初始化仓储实例
        :param model: SQLAlchemy 模型类 (如 User)
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据主键查询单条记录
        
        :return: 实体对象 或 None
        """
        # 使用 execute + scalar_one_or_none 是 SQLAlchemy 2.0 标准异步查询方式
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        分页查询多条记录
        
        :param skip: 偏移量 (Offset)
        :param limit: 限制条数 (Limit)
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录
        
        [流程] Pydantic Schema -> Dict -> DB Model -> Insert -> Refresh
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # 将字典解包映射到模型字段
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)  # 刷新以获取数据库生成的字段 (如自增 ID, created_at)
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
        更新现有记录
        
        [关键逻辑解释] exclude_unset=True
        在处理 PATCH 请求时，前端只发送修改的字段。
        若不设置 exclude_unset=True，Pydantic 会将未发送的字段解析为 None 或默认值，
        导致数据库中原本有值的数据被意外覆盖或清空。此参数确保只更新显式传递的字段。
        """
        # 1. 序列化当前数据库对象
        obj_data = jsonable_encoder(db_obj)

        # 2. 解析更新数据
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # 3. 映射修改
        for field in obj_data:
            if field in update_data:
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

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
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
