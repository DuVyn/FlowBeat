"""
音乐资源管理 API

包含艺术家、专辑的 CRUD 和音乐文件的上传接口。
同时包含用户交互事件的上报接口。
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.music import Album, Music, Playlist, PlaylistSong  # 确保导入了模型
from app.models.user import User
from app.repositories.music_repository import AlbumRepository, ArtistRepository, MusicRepository
from app.schemas.music import (
    AlbumCreate, AlbumResponse,
    ArtistCreate, ArtistResponse,
    MusicCreate, MusicResponse,
    MusicListResponse,
    InteractionCreate, InteractionResponse, LikeStatusResponse,
    PlaylistCreate, PlaylistUpdate, PlaylistResponse, PlaylistDetailResponse,
    PlaylistListResponse, AddSongToPlaylistRequest
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


@router.get("/search", response_model=MusicListResponse)
async def search_music(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        q: str = "",
        skip: int = 0,
        limit: int = 20,
):
    """
    搜索音乐

    按歌曲名称或歌手名称进行模糊搜索。
    """
    from app.models.music import Artist

    if not q.strip():
        return MusicListResponse(items=[], total=0)

    search_pattern = f"%{q}%"

    # 搜索条件：歌曲名称匹配 OR 歌手名称匹配
    stmt = (
        select(Music)
        .join(Album, Music.album_id == Album.id)
        .join(Artist, Album.artist_id == Artist.id)
        .options(selectinload(Music.album).selectinload(Album.artist))
        .where(
            (Music.title.ilike(search_pattern)) |
            (Artist.name.ilike(search_pattern))
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    # 获取总数
    count_stmt = (
        select(func.count())
        .select_from(Music)
        .join(Album, Music.album_id == Album.id)
        .join(Artist, Album.artist_id == Artist.id)
        .where(
            (Music.title.ilike(search_pattern)) |
            (Artist.name.ilike(search_pattern))
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

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


# --- Interaction Endpoints ---

@router.post("/interactions", response_model=InteractionResponse)
async def record_interaction(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
        interaction_in: InteractionCreate,
):
    """
    记录用户交互行为

    前端播放器在以下场景调用此接口:
    - PLAY: 音乐播放完成时上报
    - LIKE: 用户点击红心收藏时上报
    - SKIP: 用户跳过当前音乐时上报

    交互权重计算逻辑:
    - PLAY: 1.0 (完整播放表示有一定兴趣)
    - LIKE: 5.0 (主动收藏表示强烈偏好)
    - SKIP: 0.0 (跳过不参与正向推荐)
    """
    return await music_service.record_interaction(
        db=db,
        user_id=current_user.id,
        music_id=interaction_in.music_id,
        interaction_type_str=interaction_in.interaction_type.value,
    )


@router.get("/interactions/like-status/{music_id}", response_model=LikeStatusResponse)
async def check_like_status(
        music_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """
    检查用户是否已收藏某音乐

    用于前端播放器和音乐卡片展示收藏状态。
    """
    liked = await music_service.check_like_status(
        db=db,
        user_id=current_user.id,
        music_id=music_id,
    )
    return LikeStatusResponse(liked=liked)


@router.get("/interactions/liked", response_model=MusicListResponse)
async def get_liked_music(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
        skip: int = 0,
        limit: int = 50,
):
    """
    获取用户收藏的音乐列表

    用于前端展示用户收藏的歌曲页面。
    """
    items, total = await music_service.get_user_liked_music(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return MusicListResponse(items=items, total=total)


@router.delete("/interactions/like/{music_id}", status_code=204)
async def remove_like(
        music_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """
    取消用户对某音乐的收藏
    """
    await music_service.remove_user_like(
        db=db,
        user_id=current_user.id,
        music_id=music_id,
    )


# --- Playlist Endpoints ---

@router.post("/playlists", response_model=PlaylistResponse)
async def create_playlist(
        *,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
        playlist_in: PlaylistCreate,
):
    """创建歌单"""
    playlist = Playlist(
        name=playlist_in.name,
        description=playlist_in.description,
        user_id=str(current_user.id),
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        user_id=str(playlist.user_id),
        cover_url=playlist.cover_url,
        song_count=0,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


@router.get("/playlists", response_model=PlaylistListResponse)
async def get_user_playlists(
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
        skip: int = 0,
        limit: int = 50,
):
    """获取当前用户的歌单列表"""
    # 获取总数
    count_stmt = (
        select(func.count())
        .select_from(Playlist)
        .where(Playlist.user_id == str(current_user.id))
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # 查询歌单列表
    stmt = (
        select(Playlist)
        .where(Playlist.user_id == str(current_user.id))
        .order_by(Playlist.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    playlists = list(result.scalars().all())

    # 构建响应，计算每个歌单的歌曲数量
    items = []
    for p in playlists:
        song_count_stmt = (
            select(func.count())
            .select_from(PlaylistSong)
            .where(PlaylistSong.playlist_id == p.id)
        )
        song_count_result = await db.execute(song_count_stmt)
        song_count = song_count_result.scalar_one()

        items.append(PlaylistResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            user_id=str(p.user_id),
            cover_url=p.cover_url,
            song_count=song_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return PlaylistListResponse(items=items, total=total)


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist_detail(
        playlist_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """获取歌单详情（包含歌曲列表）"""
    from app.core.exceptions import NotFoundError, ForbiddenError

    # 查询歌单
    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise NotFoundError("歌单")

    # 检查权限：只能查看自己的歌单
    if str(playlist.user_id) != str(current_user.id):
        raise ForbiddenError("无权访问此歌单")

    # 查询歌单中的歌曲
    songs_stmt = (
        select(Music)
        .join(PlaylistSong, PlaylistSong.music_id == Music.id)
        .options(selectinload(Music.album).selectinload(Album.artist))
        .where(PlaylistSong.playlist_id == playlist_id)
        .order_by(PlaylistSong.position)
    )
    songs_result = await db.execute(songs_stmt)
    songs = list(songs_result.scalars().all())

    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        user_id=str(playlist.user_id),
        cover_url=playlist.cover_url,
        song_count=len(songs),
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        songs=songs,
    )


@router.put("/playlists/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
        playlist_id: int,
        playlist_in: PlaylistUpdate,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """更新歌单"""
    from app.core.exceptions import NotFoundError, ForbiddenError

    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise NotFoundError("歌单")

    if str(playlist.user_id) != str(current_user.id):
        raise ForbiddenError("无权修改此歌单")

    # 更新字段
    if playlist_in.name is not None:
        playlist.name = playlist_in.name
    if playlist_in.description is not None:
        playlist.description = playlist_in.description

    await db.commit()
    await db.refresh(playlist)

    # 获取歌曲数量
    song_count_stmt = (
        select(func.count())
        .select_from(PlaylistSong)
        .where(PlaylistSong.playlist_id == playlist.id)
    )
    song_count_result = await db.execute(song_count_stmt)
    song_count = song_count_result.scalar_one()

    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        user_id=str(playlist.user_id),
        cover_url=playlist.cover_url,
        song_count=song_count,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


@router.delete("/playlists/{playlist_id}", status_code=204)
async def delete_playlist(
        playlist_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """删除歌单"""
    from app.core.exceptions import NotFoundError, ForbiddenError
    from sqlalchemy import delete

    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise NotFoundError("歌单")

    if str(playlist.user_id) != str(current_user.id):
        raise ForbiddenError("无权删除此歌单")

    await db.execute(delete(Playlist).where(Playlist.id == playlist_id))
    await db.commit()


@router.post("/playlists/{playlist_id}/songs", status_code=201)
async def add_song_to_playlist(
        playlist_id: int,
        song_in: AddSongToPlaylistRequest,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """添加歌曲到歌单"""
    from app.core.exceptions import NotFoundError, ForbiddenError, BusinessError

    # 检查歌单是否存在
    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise NotFoundError("歌单")

    if str(playlist.user_id) != str(current_user.id):
        raise ForbiddenError("无权操作此歌单")

    # 检查歌曲是否存在
    music_stmt = select(Music).where(Music.id == song_in.music_id)
    music_result = await db.execute(music_stmt)
    music = music_result.scalar_one_or_none()

    if not music:
        raise NotFoundError("歌曲")

    # 检查歌曲是否已在歌单中
    exists_stmt = (
        select(PlaylistSong)
        .where(
            PlaylistSong.playlist_id == playlist_id,
            PlaylistSong.music_id == song_in.music_id,
        )
    )
    exists_result = await db.execute(exists_stmt)
    if exists_result.scalar_one_or_none():
        raise BusinessError("歌曲已在歌单中")

    # 获取当前最大位置
    max_pos_stmt = (
        select(func.coalesce(func.max(PlaylistSong.position), 0))
        .where(PlaylistSong.playlist_id == playlist_id)
    )
    max_pos_result = await db.execute(max_pos_stmt)
    max_position = max_pos_result.scalar_one()

    # 添加歌曲到歌单
    playlist_song = PlaylistSong(
        playlist_id=playlist_id,
        music_id=song_in.music_id,
        position=max_position + 1,
    )
    db.add(playlist_song)
    await db.commit()

    return {"message": "歌曲已添加到歌单"}


@router.delete("/playlists/{playlist_id}/songs/{music_id}", status_code=204)
async def remove_song_from_playlist(
        playlist_id: int,
        music_id: int,
        db: Annotated[AsyncSession, Depends(deps.get_db)],
        current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """从歌单移除歌曲"""
    from app.core.exceptions import NotFoundError, ForbiddenError
    from sqlalchemy import delete

    # 检查歌单是否存在
    stmt = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise NotFoundError("歌单")

    if str(playlist.user_id) != str(current_user.id):
        raise ForbiddenError("无权操作此歌单")

    # 删除关联
    await db.execute(
        delete(PlaylistSong)
        .where(
            PlaylistSong.playlist_id == playlist_id,
            PlaylistSong.music_id == music_id,
        )
    )
    await db.commit()
