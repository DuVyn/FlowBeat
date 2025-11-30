"""
音乐资源管理服务

本模块处理复杂的音乐上传与管理逻辑，核心是保证 MinIO 文件与 DB 元数据的一致性。
"""

import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError, NotFoundError
from app.models.music import Music
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


music_service = MusicService()
