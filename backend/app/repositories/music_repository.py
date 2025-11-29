"""
音乐资源仓储模块

本模块集中管理 Artist, Album, Music 的数据库访问。
虽然也可以拆分为三个文件，但鉴于它们聚合度极高，合并管理能减少样板代码。
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# [Fix] 确保导入 selectinload
from sqlalchemy.orm import selectinload

from app.models.music import Album, Artist, Music
from app.repositories.base import BaseRepository
from app.schemas.music import AlbumCreate, AlbumBase, ArtistCreate, ArtistBase, MusicCreate, MusicBase


class ArtistRepository(BaseRepository[Artist, ArtistCreate, ArtistBase]):
    def __init__(self):
        super().__init__(Artist)

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Artist]:
        """获取艺术家列表"""
        return await self.get_multi(db, skip=skip, limit=limit)


class AlbumRepository(BaseRepository[Album, AlbumCreate, AlbumBase]):
    def __init__(self):
        super().__init__(Album)

    async def get_by_artist(self, db: AsyncSession, artist_id: int) -> List[Album]:
        """
        获取指定艺术家的所有专辑

        [Fix] 增加 options(selectinload(Album.artist))
        原因: Pydantic 响应模型 AlbumResponse 包含嵌套的 artist 字段。
        在异步模式下，必须显式预加载关联关系，否则序列化时会触发 MissingGreenlet 错误。
        """
        stmt = select(Album).options(
            selectinload(Album.artist)
        ).where(Album.artist_id == artist_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())


class MusicRepository(BaseRepository[Music, MusicCreate, MusicBase]):
    def __init__(self):
        super().__init__(Music)

    async def get_with_details(self, db: AsyncSession, music_id: int) -> Optional[Music]:
        """
        获取音乐详情（预加载专辑和艺术家信息）

        优化说明:
        使用 selectinload 解决 N+1 查询问题。
        """
        stmt = select(Music).options(
            selectinload(Music.album).selectinload(Album.artist)
        ).where(Music.id == music_id)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()
