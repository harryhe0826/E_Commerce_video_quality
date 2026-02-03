"""
场景提取器 - 使用 PySceneDetect 进行场景切换检测
"""
import os
from typing import List, Tuple, Dict
from loguru import logger

try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False
    logger.warning("PySceneDetect not installed. 场景检测功能不可用。")


class SceneExtractor:
    """场景提取器"""

    def __init__(self, threshold: int = 27):
        """
        初始化场景提取器

        Args:
            threshold: 场景切换检测阈值 (0-255，越低越敏感)
        """
        self.threshold = threshold

    def detect_scenes(
        self,
        video_path: str,
        threshold: int = None
    ) -> List[Tuple[float, float]]:
        """
        检测视频中的场景切换

        Args:
            video_path: 视频文件路径
            threshold: 检测阈值（覆盖默认值）

        Returns:
            场景列表 [(start_time, end_time), ...]
        """
        if not SCENEDETECT_AVAILABLE:
            logger.warning("PySceneDetect not available, returning empty result")
            return []

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return []

        if threshold is None:
            threshold = self.threshold

        try:
            logger.info(f"Detecting scenes in: {video_path} (threshold={threshold})")

            # 创建视频管理器和场景管理器
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()

            # 添加场景检测器
            scene_manager.add_detector(ContentDetector(threshold=threshold))

            # 开始检测
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)

            # 获取场景列表
            scene_list = scene_manager.get_scene_list()

            # 转换为时间戳
            scenes = []
            for i, (start, end) in enumerate(scene_list):
                start_time = start.get_seconds()
                end_time = end.get_seconds()
                scenes.append((start_time, end_time))

            logger.info(f"Detected {len(scenes)} scenes")

            return scenes

        except Exception as e:
            logger.error(f"Error detecting scenes: {e}")
            return []

    def get_scene_count(self, video_path: str) -> int:
        """
        获取场景数量

        Args:
            video_path: 视频路径

        Returns:
            场景数量
        """
        scenes = self.detect_scenes(video_path)
        return len(scenes)

    def get_average_shot_length(
        self,
        video_path: str,
        total_duration: float = None
    ) -> float:
        """
        计算平均镜头长度（ASL）

        Args:
            video_path: 视频路径
            total_duration: 视频总时长（秒），如果为 None 则自动计算

        Returns:
            平均镜头长度（秒）
        """
        scenes = self.detect_scenes(video_path)

        if not scenes:
            return 0.0

        if total_duration is None:
            # 使用最后一个场景的结束时间作为总时长
            total_duration = scenes[-1][1]

        # 计算平均镜头长度
        asl = total_duration / len(scenes)
        return asl

    def get_long_shots(
        self,
        video_path: str,
        min_duration: float = 5.0
    ) -> List[Dict[str, any]]:
        """
        获取长镜头（持续时间超过阈值的镜头）

        Args:
            video_path: 视频路径
            min_duration: 最小时长（秒）

        Returns:
            长镜头列表
        """
        scenes = self.detect_scenes(video_path)

        long_shots = []
        for i, (start, end) in enumerate(scenes):
            duration = end - start
            if duration >= min_duration:
                long_shots.append({
                    "shot_number": i + 1,
                    "start": start,
                    "end": end,
                    "duration": duration
                })

        return long_shots

    def get_scene_statistics(
        self,
        video_path: str
    ) -> Dict[str, any]:
        """
        获取场景统计信息

        Args:
            video_path: 视频路径

        Returns:
            统计信息字典
        """
        scenes = self.detect_scenes(video_path)

        if not scenes:
            return {
                "total_scenes": 0,
                "average_shot_length": 0.0,
                "shortest_shot": 0.0,
                "longest_shot": 0.0,
                "total_cuts": 0
            }

        # 计算各个镜头的长度
        shot_lengths = [end - start for start, end in scenes]

        return {
            "total_scenes": len(scenes),
            "average_shot_length": sum(shot_lengths) / len(shot_lengths),
            "shortest_shot": min(shot_lengths),
            "longest_shot": max(shot_lengths),
            "total_cuts": len(scenes) - 1
        }


# 全局实例（延迟加载）
_scene_extractor_instance = None


def get_scene_extractor(threshold: int = 27) -> SceneExtractor:
    """
    获取场景提取器实例（单例模式）

    Args:
        threshold: 检测阈值

    Returns:
        SceneExtractor 实例
    """
    global _scene_extractor_instance
    if _scene_extractor_instance is None:
        _scene_extractor_instance = SceneExtractor(threshold)
    return _scene_extractor_instance
