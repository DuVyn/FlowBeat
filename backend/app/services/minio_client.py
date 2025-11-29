"""
MinIO 对象存储客户端封装

本模块封装了 minio 官方库，提供统一的文件上传与管理接口。

设计模式:
- 单例模式: 系统全局共享一个 MinioClient 实例。
- 适配器模式: 屏蔽底层 S3 协议细节，向上层提供简单的 put/remove 接口。
"""

import io
from datetime import timedelta
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.exceptions import BusinessError


class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """确保存储桶存在，若不存在则自动创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                # 设置桶策略为 public download (只读)
                # 注意: 生产环境应更严格控制权限，此处为了演示方便设为公开
                policy = f'''
                {{
                  "Version": "2012-10-17",
                  "Statement": [
                    {{
                      "Effect": "Allow",
                      "Principal": {{ "AWS": ["*"] }},
                      "Action": ["s3:GetObject"],
                      "Resource": ["arn:aws:s3:::{self.bucket_name}/*"]
                    }}
                  ]
                }}
                '''
                self.client.set_bucket_policy(self.bucket_name, policy)
        except Exception as e:
            print(f"MinIO 连接失败: {e}")

    def put_object(self, file_data: BinaryIO, file_name: str, content_type: str, length: int) -> str:
        """
        上传文件到 MinIO

        Args:
            file_data: 文件流 (BytesIO 或 SpooledTemporaryFile)
            file_name: 目标文件名 (包含路径)
            content_type: MIME 类型
            length: 文件大小

        Returns:
            str: 文件的访问 URL (相对路径或完整 URL)
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=file_data,
                length=length,
                content_type=content_type
            )
            # 构造永久访问 URL
            # 格式: http://localhost:9000/flowbeat-music/filename.mp3
            protocol = "https" if settings.MINIO_SECURE else "http"
            return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{file_name}"
        except S3Error as e:
            raise BusinessError(f"文件上传失败: {str(e)}")

    def remove_object(self, file_url: str):
        """
        删除文件 (用于回滚或清理)

        Args:
            file_url: 完整的文件 URL
        """
        try:
            # 从 URL 中提取 object_name
            # URL: http://host:port/bucket/object_name
            object_name = file_url.split(f"/{self.bucket_name}/")[-1]
            self.client.remove_object(self.bucket_name, object_name)
        except Exception as e:
            # 删除失败不应阻断主流程，记录日志即可
            print(f"Warning: Failed to cleanup orphan file {file_url}: {e}")


# 全局单例
minio_client = MinioClient()
