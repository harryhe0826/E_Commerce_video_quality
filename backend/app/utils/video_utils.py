"""
视频处理工具函数
"""
import os
import subprocess
import json
from typing import Optional, Tuple
from pathlib import Path
from loguru import logger


def get_video_info(video_path: str) -> dict:
    """
    使用 ffprobe 获取视频信息

    Args:
        video_path: 视频文件路径

    Returns:
        包含视频信息的字典
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"ffprobe error: {result.stderr}")
            return {}

        data = json.loads(result.stdout)

        # 提取视频流信息
        video_stream = next(
            (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            return {}

        # 提取关键信息
        duration = float(data.get('format', {}).get('duration', 0))
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        fps_str = video_stream.get('r_frame_rate', '0/1')

        # 计算 FPS
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 0
        except:
            fps = 0

        return {
            'duration': duration,
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}",
            'fps': int(fps),
            'codec': video_stream.get('codec_name', 'unknown')
        }

    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {}


def extract_audio(video_path: str, output_path: str) -> bool:
    """
    从视频中提取音频

    Args:
        video_path: 视频文件路径
        output_path: 输出音频文件路径

    Returns:
        是否成功
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不处理视频
            '-acodec', 'pcm_s16le',  # WAV 格式
            '-ar', '16000',  # 采样率 16kHz
            '-ac', '1',  # 单声道
            '-y',  # 覆盖输出文件
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg audio extraction error: {result.stderr}")
            return False

        logger.info(f"Audio extracted: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return False


def extract_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    """
    从视频中提取指定时间戳的帧

    Args:
        video_path: 视频文件路径
        timestamp: 时间戳（秒）
        output_path: 输出图片路径

    Returns:
        是否成功
    """
    try:
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', video_path,
            '-frames:v', '1',
            '-q:v', '2',  # 高质量
            '-y',
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg frame extraction error: {result.stderr}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error extracting frame: {e}")
        return False


def extract_key_frames(video_path: str, output_dir: str, fps: int = 1) -> list:
    """
    从视频中按指定帧率提取关键帧

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        fps: 每秒提取几帧

    Returns:
        提取的帧文件路径列表
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        # 输出文件模式
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps={fps}',  # 设置帧率
            '-q:v', '2',  # 高质量
            '-y',
            output_pattern
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg key frames extraction error: {result.stderr}")
            return []

        # 获取生成的文件列表
        frames = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith('frame_') and f.endswith('.jpg')
        ])

        logger.info(f"Extracted {len(frames)} key frames")
        return frames

    except Exception as e:
        logger.error(f"Error extracting key frames: {e}")
        return []


def convert_video(input_path: str, output_path: str,
                 codec: str = 'libx264', crf: int = 23) -> bool:
    """
    转码视频为 H.264 MP4 格式

    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        codec: 视频编码器
        crf: 质量参数（0-51，越小质量越好）

    Returns:
        是否成功
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', codec,
            '-crf', str(crf),
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',  # 优化网络播放
            '-y',
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg conversion error: {result.stderr}")
            return False

        logger.info(f"Video converted: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error converting video: {e}")
        return False


def validate_video_file(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    验证视频文件

    Args:
        file_path: 文件路径
        max_size_mb: 最大文件大小（MB）

    Returns:
        (是否有效, 错误信息)
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False, "文件不存在"

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        return False, f"文件大小超过限制（{max_size_mb}MB）"

    # 检查文件扩展名
    ext = Path(file_path).suffix.lower()
    if ext not in ['.mp4', '.mov', '.avi']:
        return False, f"不支持的文件格式：{ext}"

    # 尝试读取视频信息
    info = get_video_info(file_path)
    if not info:
        return False, "无法读取视频信息，文件可能已损坏"

    # 检查视频时长
    duration = info.get('duration', 0)
    if duration < 5:
        return False, "视频时长过短（至少5秒）"
    if duration > 120:
        return False, "视频时长过长（最多120秒）"

    return True, ""
