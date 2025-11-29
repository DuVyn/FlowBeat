"""
音乐资源领域模型模块

本模块定义了音乐资源子域的核心实体:
1. Artist (艺术家) - 聚合根之一
2. Album (专辑) - 属于艺术家
3. Music (音乐) - 属于专辑

设计原则:
1. 完整性约束: 使用外键 (ForeignKey) 强制维护实体间的关联关系。
2. 级联操作: 配置 relationship 的 cascade 属性，便于级联查询。
3. 性能优化: 关键字段 (title, name) 建立索引以加速模糊搜索。
"""

from datetime import date, datetime
from typing import List, Optional

# 引入 DateTime 用于显式指定时区类型
from sqlalchemy import Date, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import _get_utc_now


class Artist(Base):
    """
    艺术家实体
    """
    __tablename__ = "artists"

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 显式指定 DateTime(timezone=True) 以支持 UTC 时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now)

    # 反向关联: 一个艺术家有多个专辑
    albums: Mapped[List["Album"]] = relationship(back_populates="artist", cascade="all, delete-orphan")


class Album(Base):
    """
    专辑实体
    """
    __tablename__ = "albums"

    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    cover_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 外键: 必须归属于一个艺术家
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), nullable=False)

    # 显式指定 DateTime(timezone=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now)

    # 关联定义
    artist: Mapped["Artist"] = relationship(back_populates="albums")
    musics: Mapped[List["Music"]] = relationship(back_populates="album", cascade="all, delete-orphan")


class Music(Base):
    """
    音乐/曲目实体
    """
    __tablename__ = "musics"

    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, comment="时长(秒)")
    track_number: Mapped[int] = mapped_column(Integer, default=1)

    # 核心字段: 存储在 MinIO 中的文件对象路径或 URL
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)

    # 外键: 必须归属于一张专辑
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False)

    # 显式指定 DateTime(timezone=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now)

    # 关联定义
    album: Mapped["Album"] = relationship(back_populates="musics")
