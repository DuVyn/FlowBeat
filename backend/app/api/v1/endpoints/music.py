"""
音乐资源管理 API

包含艺术家、专辑的 CRUD 和音乐文件的上传接口。
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.music import Album, Music  # 确保导入了模型
from app.models.user import User
from app.repositories.music_repository import AlbumRepository, ArtistRepository, MusicRepository
from app.schemas.music import (
    AlbumCreate, AlbumResponse,
    ArtistCreate, ArtistResponse,
    MusicCreate, MusicResponse,
    MusicListResponse
)
from app.services.music_service import music_service

router = APIRouter()


# --- Artist Endpoints ---

@router.post("/artists", response_model=ArtistResponse)
async def create_artist(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        artist_in: ArtistCreate,
        current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
):
    """创建艺术家 (仅管理员)"""
    repo = ArtistRepository()
    return await repo.create(db, obj_in=artist_in)


@router.get("/artists", response_model=List[ArtistResponse])
async def read_artists(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        skip: int = 0,
        limit: int = 100,
):
    """获取艺术家列表 (公开)"""
    repo = ArtistRepository()
    return await repo.get_all(db, skip=skip, limit=limit)


# --- Album Endpoints ---

@router.post("/albums", response_model=AlbumResponse)
async def create_album(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        album_in: AlbumCreate,
        current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
):
    """创建专辑 (仅管理员)"""
    repo = AlbumRepository()
    new_album = await repo.create(db, obj_in=album_in)

    # 显式加载关联的 artist，解决 MissingGreenlet 错误
    # 因为 Pydantic 响应模型需要嵌套的 artist 信息
    stmt = select(Album).options(selectinload(Album.artist)).where(Album.id == new_album.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/artists/{artist_id}/albums", response_model=List[AlbumResponse])
async def read_artist_albums(
        artist_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
):
    """获取某艺术家的所有专辑"""
    repo = AlbumRepository()
    return await repo.get_by_artist(db, artist_id=artist_id)


# --- Music Endpoints ---

@router.post("/upload", response_model=MusicResponse)
async def upload_music(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
        file: Annotated[UploadFile, File(...)],
        title: Annotated[str, Form(...)],
        duration: Annotated[int, Form(...)],
        album_id: Annotated[int, Form(...)],
        track_number: Annotated[int, Form()] = 1,
):
    """
    上传音乐文件 (仅管理员)
    """
    # 构造 Schema 进行数据校验
    music_meta = MusicCreate(
        title=title,
        duration=duration,
        album_id=album_id,
        track_number=track_number
    )

    # 调用 Service 执行事务
    new_music = await music_service.upload_music(db, file, music_meta)

    # 显式加载关联的 album 和 album.artist
    # 因为 Pydantic 响应模型需要嵌套的 album 信息
    stmt = select(Music).options(
        selectinload(Music.album).selectinload(Album.artist)
    ).where(Music.id == new_music.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/", response_model=MusicListResponse)
async def read_musics(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        skip: int = 0,
        limit: int = 100,
):
    """获取音乐列表 (分页)"""
    # 获取总数
    count_stmt = select(func.count()).select_from(Music)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # 列表查询也需要预加载，否则序列化时会报错
    # 这里的 repo.get_multi 默认没有预加载，我们需要重写一下查询
    stmt = select(Music).options(
        selectinload(Music.album).selectinload(Album.artist)
    ).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return MusicListResponse(items=items, total=total)


# DELETE 接口
@router.delete("/{music_id}", status_code=204)
async def delete_music(
        music_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        # 权限校验: 仅管理员可删除
        current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
):
    """
    删除音乐
    """
    await music_service.delete_music(db, music_id)
