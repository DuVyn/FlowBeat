"""
音乐资源领域模型模块

本模块定义了音乐资源子域的核心实体:
1. Artist (艺术家) - 聚合根之一
2. Album (专辑) - 属于艺术家
3. Music (音乐) - 属于专辑
4. Playlist (歌单) - 用户创建的歌单
5. PlaylistSong (歌单歌曲关联) - 歌单与歌曲的多对多关联

设计原则:
1. 完整性约束: 使用外键 (ForeignKey) 强制维护实体间的关联关系。
2. 级联操作: 配置 relationship 的 cascade 属性，便于级联查询。
3. 性能优化: 关键字段 (title, name) 建立索引以加速模糊搜索。
"""

from datetime import date, datetime
from typing import List, Optional

# 引入 DateTime 用于显式指定时区类型
from sqlalchemy import Date, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
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


class Playlist(Base):
    """
    用户歌单实体

    支持用户创建自己的歌单，组织收藏的歌曲。
    """
    __tablename__ = "playlists"

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 外键: 歌单属于某个用户
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False).with_variant(UUID, "postgresql"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now, onupdate=_get_utc_now)

    # 关联定义: 歌单包含多首歌曲
    songs: Mapped[List["PlaylistSong"]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistSong.position"
    )


class PlaylistSong(Base):
    """
    歌单与歌曲的关联实体

    实现歌单与歌曲的多对多关系，并支持歌曲在歌单中的排序。
    """
    __tablename__ = "playlist_songs"

    # 外键: 关联歌单
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 外键: 关联歌曲
    music_id: Mapped[int] = mapped_column(
        ForeignKey("musics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 歌曲在歌单中的位置
    position: Mapped[int] = mapped_column(Integer, default=0)

    # 添加时间
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_get_utc_now)

    # 关联定义
    playlist: Mapped["Playlist"] = relationship(back_populates="songs")
    music: Mapped["Music"] = relationship()
