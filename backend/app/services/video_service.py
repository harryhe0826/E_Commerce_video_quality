"""
视频处理服务
"""
import os
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from loguru import logger

from app.db import Video
from app.config import settings
from app.services.storage_service import storage_service
from app.utils.video_utils import (
    get_video_info,
    extract_audio,
    extract_key_frames,
    convert_video,
    validate_video_file
)


class VideoService:
    """视频处理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def save_uploaded_video(self, file_content: bytes, filename: str) -> tuple[str, str]:
        """
        保存上传的视频文件（到 R2 或本地）

        Args:
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            (video_id, file_url_or_path)
        """
        # 生成唯一 ID
        video_id = f"vid_{uuid.uuid4().hex[:12]}"

        # 保留原始扩展名
        ext = Path(filename).suffix
        new_filename = f"{video_id}{ext}"

        # 构建对象键（用于 R2）或文件路径（用于本地存储）
        object_key = f"videos/{new_filename}"

        # 确定 content_type
        content_type_map = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
        }
        content_type = content_type_map.get(ext.lower(), 'application/octet-stream')

        # 使用存储服务上传（自动处理 R2 或本地存储）
        file_url = storage_service.upload_file(file_content, object_key, content_type)

        if not file_url:
            raise Exception("Failed to upload video to storage")

        logger.info(f"Video saved: {file_url}")
        return video_id, file_url

    def process_video(self, video_id: str, file_url: str, filename: str) -> dict:
        """
        处理上传的视频

        Args:
            video_id: 视频 ID
            file_url: 文件 URL（R2）或本地路径
            filename: 原始文件名

        Returns:
            处理结果字典
        """
        temp_file_path = None

        try:
            # 1. 如果使用 R2，需要下载到临时文件进行分析
            if settings.USE_R2_STORAGE:
                # 从 URL 提取 object_key
                # file_url 格式: https://bucket.account.r2.cloudflarestorage.com/videos/vid_xxx.mp4
                # 或: https://custom-domain.com/videos/vid_xxx.mp4
                # 我们需要提取 "videos/vid_xxx.mp4" 部分
                if '/videos/' in file_url:
                    object_key = file_url.split('/videos/', 1)[1]
                    object_key = f"videos/{object_key}"
                else:
                    # 如果无法提取，使用 video_id 构建
                    ext = Path(filename).suffix
                    object_key = f"videos/{video_id}{ext}"

                # 下载到临时文件
                ext = Path(filename).suffix
                temp_file_path = storage_service.create_temp_file_from_r2(object_key, suffix=ext)

                if not temp_file_path:
                    return {
                        'success': False,
                        'error': '无法从存储下载视频文件'
                    }

                file_path = temp_file_path
            else:
                # 本地存储，file_url 就是本地路径
                file_path = file_url

            # 2. 验证视频文件
            logger.info(f"Validating video: {video_id}")
            is_valid, error_msg = validate_video_file(
                file_path,
                max_size_mb=settings.MAX_VIDEO_SIZE_MB
            )

            if not is_valid:
                logger.error(f"Video validation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            # 3. 提取视频信息
            logger.info(f"Extracting video info: {video_id}")
            video_info = get_video_info(file_path)

            if not video_info:
                return {
                    'success': False,
                    'error': '无法读取视频信息'
                }

            # 4. 获取文件大小
            file_size = os.path.getsize(file_path)

            # 5. 保存视频记录到数据库（存储 R2 URL 或本地路径）
            video = Video(
                id=video_id,
                filename=filename,
                file_path=file_url,  # 存储 R2 URL 或本地路径
                duration=video_info.get('duration'),
                resolution=video_info.get('resolution'),
                fps=video_info.get('fps'),
                file_size=file_size,
                status='uploaded'
            )

            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)

            logger.info(f"Video record saved to database: {video_id}")

            # 6. 预处理（可选）- 提取音频和关键帧
            # 这部分可以在分析时再做，上传阶段暂时跳过
            # self._preprocess_video(video_id, file_path)

            return {
                'success': True,
                'video': video,
                'info': video_info
            }

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")

    def _preprocess_video(self, video_id: str, file_path: str):
        """
        预处理视频：提取音频和关键帧

        Args:
            video_id: 视频 ID
            file_path: 视频文件路径
        """
        try:
            # 创建临时目录
            video_temp_dir = os.path.join(settings.TEMP_DIR, video_id)
            os.makedirs(video_temp_dir, exist_ok=True)

            # 提取音频
            audio_path = os.path.join(video_temp_dir, "audio.wav")
            logger.info(f"Extracting audio for {video_id}")
            extract_audio(file_path, audio_path)

            # 提取关键帧（每秒1帧）
            frames_dir = os.path.join(video_temp_dir, "frames")
            logger.info(f"Extracting key frames for {video_id}")
            extract_key_frames(file_path, frames_dir, fps=1)

            logger.info(f"Preprocessing completed for {video_id}")

        except Exception as e:
            logger.error(f"Error preprocessing video {video_id}: {e}")

    def get_video(self, video_id: str) -> Video:
        """
        获取视频记录

        Args:
            video_id: 视频 ID

        Returns:
            Video 对象
        """
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_video_list(self, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        """
        获取视频列表

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数

        Returns:
            (视频列表, 总数)
        """
        total = self.db.query(Video).count()
        videos = (
            self.db.query(Video)
            .order_by(Video.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return videos, total

    def delete_video(self, video_id: str) -> bool:
        """
        删除视频

        Args:
            video_id: 视频 ID

        Returns:
            是否成功
        """
        try:
            video = self.get_video(video_id)
            if not video:
                return False

            # 删除文件（从 R2 或本地）
            if settings.USE_R2_STORAGE:
                # 从 file_path (R2 URL) 提取 object_key
                if '/videos/' in video.file_path:
                    object_key = video.file_path.split('/videos/', 1)[1]
                    object_key = f"videos/{object_key}"
                    storage_service.delete_file(object_key)
            else:
                # 删除本地文件
                if os.path.exists(video.file_path):
                    os.remove(video.file_path)

            # 删除临时文件
            video_temp_dir = os.path.join(settings.TEMP_DIR, video_id)
            if os.path.exists(video_temp_dir):
                import shutil
                shutil.rmtree(video_temp_dir)

            # 删除数据库记录
            self.db.delete(video)
            self.db.commit()

            logger.info(f"Video deleted: {video_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {e}")
            self.db.rollback()
            return False
