"""
音乐资源管理服务

本模块处理复杂的音乐上传与管理逻辑，核心是保证 MinIO 文件与 DB 元数据的一致性。
同时处理用户交互行为的记录与权重计算。
"""

import uuid
from typing import BinaryIO
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError, NotFoundError
from app.models.interaction import Interaction, InteractionType, INTERACTION_WEIGHTS
from app.models.music import Music
from app.repositories.interaction_repository import interaction_repository
from app.repositories.music_repository import MusicRepository
from app.schemas.music import MusicCreate
from app.services.minio_client import minio_client


class MusicService:
    def __init__(self):
        self.music_repo = MusicRepository()

    async def upload_music(
            self,
            db: AsyncSession,
            file: UploadFile,
            metadata: MusicCreate
    ) -> Music:
        """
        上传音乐事务编排 (Saga Pattern Lite)

        步骤:
        1. 验证文件格式。
        2. [Action] 上传文件至 MinIO (不可回滚的操作)。
        3. [Action] 写入数据库 (可回滚的操作)。
        4. [Compensation] 若 DB 写入失败，删除 MinIO 中的文件。

        Args:
            db: 数据库会话
            file: 上传的文件对象
            metadata: 音乐元数据 (Title, AlbumID 等)

        Returns:
            Music: 创建成功的音乐实体
        """
        # 1. 基础校验
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise BusinessError("仅支持上传音频文件")

        # 生成唯一文件名，防止覆盖: uuid + 原始扩展名
        # 当 filename 为 None 或不包含扩展名时，使用默认扩展名
        file_ext = "mp3"  # 默认扩展名
        if file.filename and "." in file.filename:
            file_ext = file.filename.split(".")[-1]
        object_name = f"music/{uuid.uuid4()}.{file_ext}"

        # 获取文件大小 (需移动指针到末尾再复位)
        # 使用底层的 SpooledTemporaryFile 对象进行 seek 操作，因为它支持 whence 参数
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        uploaded_url = ""

        try:
            # 2. 执行 MinIO 上传
            # 注意: file.file 是 Python 的 SpooledTemporaryFile 对象
            uploaded_url = minio_client.put_object(
                file_data=file.file,
                file_name=object_name,
                content_type=file.content_type,
                length=file_size
            )

            # 3. 准备 DB 实体数据
            # Schema 不包含 file_url，需要手动注入
            music_in_data = metadata.model_dump()
            db_obj = Music(**music_in_data, file_url=uploaded_url)

            # 4. 执行 DB 写入
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            return db_obj

        except Exception as e:
            # 5. 补偿事务 (Compensating Transaction)
            # 先回滚数据库事务，确保会话状态一致
            await db.rollback()

            # 如果 MinIO 上传成功了，但后续 DB 操作失败 (如外键错误)，必须删除 MinIO 文件
            if uploaded_url:
                print(f"检测到事务失败，正在回滚 MinIO 文件: {uploaded_url}")
                minio_client.remove_object(uploaded_url)

            # 重新抛出异常，触发 FastAPI 的 HTTP 错误响应
            raise BusinessError(f"音乐上传失败: {str(e)}")

    async def delete_music(self, db: AsyncSession, music_id: int) -> None:
        """
        删除音乐 (包含文件清理)
        策略: 先删除 DB 记录，成功后再删除 MinIO 文件。
        这样即使 MinIO 删除失败，也只是产生孤儿文件，而不会导致用户看到无法播放的死链。
        """

        # 1. 获取实体以拿到 file_url
        music = await self.music_repo.get(db, music_id)
        if not music:
            raise NotFoundError("音乐文件")

        file_url = music.file_url

        # 2. 删除数据库记录 (这是一个事务操作)
        await self.music_repo.remove(db, id=music_id)

        # 3. 数据库删除成功后，清理 MinIO 对象
        # 注意：如果此处失败，会产生孤儿文件，建议生产环境接入异步任务队列重试清理
        if file_url:
            try:
                minio_client.remove_object(file_url)
            except Exception as e:
                # 记录日志即可，不要阻断主流程，因为业务上该资源已不存在
                print(f"Warning: Failed to cleanup file {file_url}: {e}")

    async def record_interaction(
            self,
            db: AsyncSession,
            user_id: UUID,
            music_id: int,
            interaction_type_str: str,
    ) -> Interaction:
        """
        记录用户交互行为

        处理交互权重计算逻辑:
        1. 将前端传入的交互类型字符串转换为枚举
        2. 根据交互类型查找对应的算法权重
        3. 调用仓储层持久化交互记录

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            music_id: 音乐 ID
            interaction_type_str: 交互类型字符串 (PLAY/LIKE/SKIP)

        Returns:
            Interaction: 创建的交互记录

        Raises:
            BusinessError: 当交互类型无效时
        """
        # 验证交互类型合法性
        try:
            interaction_type = InteractionType(interaction_type_str)
        except ValueError:
            raise BusinessError(f"无效的交互类型: {interaction_type_str}")

        # 验证音乐是否存在
        music = await self.music_repo.get(db, music_id)
        if not music:
            raise NotFoundError("音乐文件")

        # 调用仓储层记录交互
        return await interaction_repository.record_interaction(
            db=db,
            user_id=user_id,
            music_id=music_id,
            interaction_type=interaction_type,
        )

    async def check_like_status(
            self,
            db: AsyncSession,
            user_id: UUID,
            music_id: int,
    ) -> bool:
        """
        检查用户是否已收藏某音乐

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            music_id: 音乐 ID

        Returns:
            bool: 是否已收藏
        """
        return await interaction_repository.check_user_liked_music(
            db=db,
            user_id=user_id,
            music_id=music_id,
        )

    async def get_user_liked_music(
            self,
            db: AsyncSession,
            user_id: UUID,
            skip: int = 0,
            limit: int = 100,
    ) -> tuple[list[Music], int]:
        """
        获取用户收藏的音乐列表

        Args:
            db: 数据库会话
            user_id: 用户 UUID
            skip: 跳过的记录数
            limit: 返回数量限制

        Returns:
            tuple[list[Music], int]: 音乐列表和总数
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.music import Album

        # 获取总数
        total = await interaction_repository.count_user_liked_music(db, user_id)

        # 获取收藏的音乐 ID 列表
        music_ids = await interaction_repository.get_user_liked_music_ids(
            db=db,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        if not music_ids:
            return [], total

        # 查询音乐详情
        stmt = (
            select(Music)
            .options(selectinload(Music.album).selectinload(Album.artist))
            .where(Music.id.in_(music_ids))
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        # 按照 music_ids 的顺序排序
        id_to_music = {m.id: m for m in items}
        sorted_items = [id_to_music[mid] for mid in music_ids if mid in id_to_music]

        return sorted_items, total

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
        return await interaction_repository.remove_user_like(
            db=db,
            user_id=user_id,
            music_id=music_id,
        )


music_service = MusicService()
