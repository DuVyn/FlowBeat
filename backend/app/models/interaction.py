"""
用户交互实体模块

本模块定义用户与音乐交互的数据模型，用于:
1. 记录用户行为（播放、收藏、跳过）
2. 为推荐算法提供隐式反馈数据

设计原则:
1. 隐式反馈采集: 自动记录用户行为，无需显式评分
2. 权重量化: 不同交互类型对应不同的算法权重
3. 时序追踪: 记录交互时间，支持时间衰减计算
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import _get_utc_now


class InteractionType(str, Enum):
    """
    交互类型枚举

    为什么定义权重映射:
    不同交互类型反映用户对音乐的不同偏好程度，
    需要量化为数值权重用于协同过滤算法的相似度计算。

    权重设计依据:
    - PLAY (1.0): 完整播放表示用户对音乐有一定兴趣
    - LIKE (5.0): 主动收藏表示强烈偏好，权重最高
    - SKIP (0.0): 跳过表示不感兴趣，不参与正向推荐
    """
    PLAY = "PLAY"
    LIKE = "LIKE"
    SKIP = "SKIP"


# 交互类型对应的算法权重映射表
# 集中管理权重值，便于后续调优
INTERACTION_WEIGHTS: dict[InteractionType, float] = {
    InteractionType.PLAY: 1.0,
    InteractionType.LIKE: 5.0,
    InteractionType.SKIP: 0.0,
}


class Interaction(Base):
    """
    用户交互实体

    记录用户与音乐的每一次交互行为，是推荐系统的核心数据来源。

    设计决策:
    1. 保留原始交互记录: 不做聚合，保留完整的时序信息
    2. 预计算权重: 存储计算后的权重值，避免查询时重复计算
    3. 外键约束: 确保数据完整性，防止孤儿记录
    """
    __tablename__ = "interactions"

    # 用户外键: 关联到用户表
    # 使用 UUID 类型匹配 User.id 的类型
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False).with_variant(UUID, "postgresql"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 音乐外键: 关联到音乐表
    music_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("musics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 交互类型: 使用枚举确保数据合法性
    interaction_type: Mapped[InteractionType] = mapped_column(
        SAEnum(InteractionType, name="interaction_type_enum"),
        nullable=False,
    )

    # 算法权重: 存储交互对应的权重值
    # 为什么存储而非实时计算:
    # 1. 推荐算法需要批量读取权重，预存储可提升查询性能
    # 2. 支持未来对权重的个性化调整（如时间衰减）
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # 交互时间: 精确记录交互发生时刻
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_get_utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Interaction(user={self.user_id}, music={self.music_id}, type={self.interaction_type})>"