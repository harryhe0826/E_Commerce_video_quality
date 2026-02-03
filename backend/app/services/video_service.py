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
        保存上传的视频文件

        Args:
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            (video_id, file_path)
        """
        # 生成唯一 ID
        video_id = f"vid_{uuid.uuid4().hex[:12]}"

        # 保留原始扩展名
        ext = Path(filename).suffix
        new_filename = f"{video_id}{ext}"

        # 保存文件
        file_path = os.path.join(settings.UPLOAD_DIR, new_filename)

        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"Video saved: {file_path}")
        return video_id, file_path

    def process_video(self, video_id: str, file_path: str, filename: str) -> dict:
        """
        处理上传的视频

        Args:
            video_id: 视频 ID
            file_path: 文件路径
            filename: 原始文件名

        Returns:
            处理结果字典
        """
        try:
            # 1. 验证视频文件
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

            # 2. 提取视频信息
            logger.info(f"Extracting video info: {video_id}")
            video_info = get_video_info(file_path)

            if not video_info:
                return {
                    'success': False,
                    'error': '无法读取视频信息'
                }

            # 3. 保存视频记录到数据库
            file_size = os.path.getsize(file_path)

            video = Video(
                id=video_id,
                filename=filename,
                file_path=file_path,
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

            # 4. 预处理（可选）- 提取音频和关键帧
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

            # 删除文件
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
