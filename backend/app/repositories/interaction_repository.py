"""
交互数据仓储模块

本模块实现用户交互数据的持久化逻辑，专注于:
1. 高效写入交互日志
2. 批量查询用于推荐算法

设计原则:
1. 写入优化: 交互数据写入频繁，需优化插入性能
2. 批量读取: 推荐算法需要批量读取数据，需优化查询效率
"""

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction, InteractionType, INTERACTION_WEIGHTS
from app.repositories.base import BaseRepository


class InteractionRepository(BaseRepository[Interaction, Any, Any]):
    """
    交互数据仓储

    继承通用 CRUD 基类，扩展交互特定的查询方法。
    """

    def __init__(self):
        super().__init__(Interaction)

    async def record_interaction(
        self,
        db: AsyncSession,
        user_id: UUID,
        music_id: int,
        interaction_type: InteractionType,
    ) -> Interaction:
        """
        记录用户交互行为

        为什么不使用 create 方法:
        交互记录需要自动计算权重值，封装此逻辑避免调用方重复处理。

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            music_id: 音乐 ID
            interaction_type: 交互类型

        Returns:
            Interaction: 创建的交互记录
        """
        # 根据交互类型获取对应权重
        weight = INTERACTION_WEIGHTS.get(interaction_type, 0.0)

        interaction = Interaction(
            user_id=str(user_id),
            music_id=music_id,
            interaction_type=interaction_type,
            weight=weight,
        )

        db.add(interaction)
        await db.commit()
        await db.refresh(interaction)

        return interaction

    async def get_user_interactions(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 100,
    ) -> List[Interaction]:
        """
        获取用户的交互历史

        用于推荐算法分析用户偏好。

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            limit: 返回数量限制

        Returns:
            List[Interaction]: 交互记录列表，按时间倒序
        """
        stmt = (
            select(Interaction)
            .where(Interaction.user_id == str(user_id))
            .order_by(Interaction.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_interactions_for_algorithm(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10000,
    ) -> List[Interaction]:
        """
        批量获取交互数据用于算法计算

        为什么设置大 limit:
        协同过滤算法需要全量数据构建相似度矩阵，
        但需要分批读取避免内存溢出。

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回数量限制

        Returns:
            List[Interaction]: 交互记录列表
        """
        stmt = (
            select(Interaction)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def check_user_liked_music(
        self,
        db: AsyncSession,
        user_id: UUID,
        music_id: int,
    ) -> bool:
        """
        检查用户是否已收藏某音乐

        用于前端展示收藏状态。

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            music_id: 音乐 ID

        Returns:
            bool: 是否已收藏
        """
        stmt = (
            select(Interaction)
            .where(
                Interaction.user_id == str(user_id),
                Interaction.music_id == music_id,
                Interaction.interaction_type == InteractionType.LIKE,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_user_liked_music_ids(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[int]:
        """
        获取用户收藏的音乐 ID 列表

        用于查询用户收藏的歌曲。

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            skip: 跳过的记录数
            limit: 返回数量限制

        Returns:
            List[int]: 音乐 ID 列表
        """
        stmt = (
            select(Interaction.music_id)
            .where(
                Interaction.user_id == str(user_id),
                Interaction.interaction_type == InteractionType.LIKE,
            )
            .order_by(Interaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .distinct()
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_user_liked_music(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """
        统计用户收藏的音乐数量

        Args:
            db: 数据库会话
            user_id: 用户 UUID

        Returns:
            int: 收藏数量
        """
        from sqlalchemy import func
        stmt = (
            select(func.count(func.distinct(Interaction.music_id)))
            .where(
                Interaction.user_id == str(user_id),
                Interaction.interaction_type == InteractionType.LIKE,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def remove_user_like(
        self,
        db: AsyncSession,
        user_id: UUID,
        music_id: int,
    ) -> bool:
        """
        取消用户对某音乐的收藏

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            music_id: 音乐 ID

        Returns:
            bool: 是否成功删除
        """
        from sqlalchemy import delete
        stmt = (
            delete(Interaction)
            .where(
                Interaction.user_id == str(user_id),
                Interaction.music_id == music_id,
                Interaction.interaction_type == InteractionType.LIKE,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0


# 单例实例，便于依赖注入
interaction_repository = InteractionRepository()