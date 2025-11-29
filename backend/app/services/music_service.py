"""
音乐资源管理服务

本模块处理复杂的音乐上传与管理逻辑，核心是保证 MinIO 文件与 DB 元数据的一致性。
"""

import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
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
        await file.seek(0, 2)
        file_size = await file.tell()
        await file.seek(0)

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


music_service = MusicService()
