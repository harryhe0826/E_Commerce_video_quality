"""
Cloudflare R2 对象存储服务
"""
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from loguru import logger
from typing import Optional
import tempfile
import os

from app.config import settings


class StorageService:
    """对象存储服务类（支持 Cloudflare R2）"""

    def __init__(self):
        self.use_r2 = settings.USE_R2_STORAGE

        if self.use_r2:
            # 配置 R2 客户端（使用 S3 兼容 API）
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
            self.bucket_name = settings.R2_BUCKET_NAME
            logger.info(f"R2 Storage Service initialized with bucket: {self.bucket_name}")
        else:
            self.s3_client = None
            logger.info("Using local file storage (R2 disabled)")

    def upload_file(self, file_content: bytes, object_key: str, content_type: str = 'video/mp4') -> Optional[str]:
        """
        上传文件到 R2

        Args:
            file_content: 文件内容（字节）
            object_key: 对象键（文件路径）
            content_type: 内容类型

        Returns:
            文件的 URL，如果失败则返回 None
        """
        if not self.use_r2:
            # 如果不使用 R2，返回本地文件路径
            local_path = os.path.join(settings.UPLOAD_DIR, object_key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_content)
            return local_path

        try:
            # 上传到 R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )

            # 构建公共 URL
            if settings.R2_PUBLIC_URL:
                file_url = f"{settings.R2_PUBLIC_URL}/{object_key}"
            else:
                # 如果没有配置公共域名，使用 R2 的默认 URL
                file_url = f"https://{self.bucket_name}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{object_key}"

            logger.info(f"File uploaded to R2: {object_key}")
            return file_url

        except ClientError as e:
            logger.error(f"Error uploading file to R2: {e}")
            return None

    def download_file(self, object_key: str, local_path: str) -> bool:
        """
        从 R2 下载文件到本地临时位置（用于分析）

        Args:
            object_key: 对象键
            local_path: 本地保存路径

        Returns:
            是否成功
        """
        if not self.use_r2:
            # 如果不使用 R2，object_key 就是本地路径
            return os.path.exists(object_key)

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 从 R2 下载
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=local_path
            )

            logger.info(f"File downloaded from R2: {object_key} -> {local_path}")
            return True

        except ClientError as e:
            logger.error(f"Error downloading file from R2: {e}")
            return False

    def delete_file(self, object_key: str) -> bool:
        """
        从 R2 删除文件

        Args:
            object_key: 对象键

        Returns:
            是否成功
        """
        if not self.use_r2:
            # 如果不使用 R2，删除本地文件
            try:
                if os.path.exists(object_key):
                    os.remove(object_key)
                return True
            except Exception as e:
                logger.error(f"Error deleting local file: {e}")
                return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            logger.info(f"File deleted from R2: {object_key}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting file from R2: {e}")
            return False

    def get_signed_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        生成签名 URL（用于临时访问）

        Args:
            object_key: 对象键
            expires_in: 过期时间（秒），默认 1 小时

        Returns:
            签名 URL，如果失败则返回 None
        """
        if not self.use_r2:
            # 如果不使用 R2，返回本地文件路径
            return object_key

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )

            logger.debug(f"Generated signed URL for {object_key}")
            return url

        except ClientError as e:
            logger.error(f"Error generating signed URL: {e}")
            return None

    def create_temp_file_from_r2(self, object_key: str, suffix: str = '.mp4') -> Optional[str]:
        """
        从 R2 下载文件到临时文件（用于视频分析）

        Args:
            object_key: 对象键
            suffix: 文件后缀

        Returns:
            临时文件路径，如果失败则返回 None
        """
        if not self.use_r2:
            # 如果不使用 R2，object_key 就是本地路径
            return object_key if os.path.exists(object_key) else None

        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                dir=settings.TEMP_DIR
            )
            temp_path = temp_file.name
            temp_file.close()

            # 下载到临时文件
            if self.download_file(object_key, temp_path):
                return temp_path
            else:
                # 如果下载失败，删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None

        except Exception as e:
            logger.error(f"Error creating temp file from R2: {e}")
            return None


# 创建全局存储服务实例
storage_service = StorageService()
