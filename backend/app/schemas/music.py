"""
音乐资源 DTO 模块

设计原则:
1. 嵌套序列化: 响应模型中包含关联对象的详细信息 (如 MusicResponse 包含 Album 信息)。
2. 校验逻辑: 确保发行日期不早于第一张唱片诞生的时间 (1860年)。
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- Artist Schemas ---
class ArtistBase(BaseModel):
    name: str = Field(..., max_length=100, description="艺术家姓名")
    bio: Optional[str] = Field(None, description="简介")


class ArtistCreate(ArtistBase):
    pass


class ArtistResponse(ArtistBase):
    id: int
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Album Schemas ---
class AlbumBase(BaseModel):
    title: str = Field(..., max_length=100, description="专辑标题")
    release_date: date = Field(..., description="发行日期")

    @field_validator('release_date')
    @classmethod
    def validate_date(cls, v: date) -> date:
        if v.year < 1860:
            raise ValueError('发行日期不能早于 1860 年')
        return v


class AlbumCreate(AlbumBase):
    artist_id: int = Field(..., description="所属艺术家ID")


class AlbumResponse(AlbumBase):
    id: int
    artist_id: int
    cover_url: Optional[str] = None
    artist: Optional[ArtistResponse] = None  # 嵌套返回
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Music Schemas ---
class MusicBase(BaseModel):
    title: str = Field(..., max_length=100, description="歌曲标题")
    duration: int = Field(..., gt=0, description="时长(秒)")
    track_number: int = Field(1, ge=1, description="音轨号")


class MusicCreate(MusicBase):
    album_id: int = Field(..., description="所属专辑ID")
    # 注意: 文件上传不通过 JSON Body，而是通过 Multipart Form，此处仅包含元数据


class MusicResponse(MusicBase):
    id: int
    file_url: str
    album: Optional[AlbumResponse] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
