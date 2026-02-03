"""
音频特征提取器 - 使用 Whisper 进行语音识别
"""
import os
from typing import Optional, List, Dict
from loguru import logger

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed. ASR功能不可用。")


class AudioExtractor:
    """音频特征提取器"""

    def __init__(self, model_name: str = "base"):
        """
        初始化音频提取器

        Args:
            model_name: Whisper 模型名称 (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None

        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Loading Whisper model: {model_name}")
                self.model = whisper.load_model(model_name)
                logger.info(f"Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
        else:
            logger.warning("Whisper not available, ASR功能将被禁用")

    def extract_text(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, any]:
        """
        从音频中提取文本和时间戳

        Args:
            audio_path: 音频文件路径
            language: 语言代码（zh, en 等），None 为自动检测

        Returns:
            包含文本和时间戳信息的字典
        """
        if not WHISPER_AVAILABLE or self.model is None:
            logger.warning("Whisper not available, returning empty result")
            return {
                "text": "",
                "segments": [],
                "language": "unknown"
            }

        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return {
                "text": "",
                "segments": [],
                "language": "unknown"
            }

        try:
            logger.info(f"Transcribing audio: {audio_path}")

            # 转录音频
            result = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                verbose=False
            )

            # 提取文本
            full_text = result.get("text", "").strip()

            # 提取分段信息
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": segment.get("words", [])
                })

            detected_language = result.get("language", "unknown")

            logger.info(f"Transcription completed. Text length: {len(full_text)}, "
                       f"Segments: {len(segments)}, Language: {detected_language}")

            return {
                "text": full_text,
                "segments": segments,
                "language": detected_language
            }

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {
                "text": "",
                "segments": [],
                "language": "unknown"
            }

    def extract_text_in_timerange(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        language: Optional[str] = None
    ) -> str:
        """
        提取指定时间范围内的文本

        Args:
            audio_path: 音频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            language: 语言代码

        Returns:
            该时间范围内的文本
        """
        result = self.extract_text(audio_path, language)

        # 筛选时间范围内的文本
        filtered_text = []
        for segment in result["segments"]:
            seg_start = segment["start"]
            seg_end = segment["end"]

            # 判断是否在时间范围内
            if seg_end >= start_time and seg_start <= end_time:
                filtered_text.append(segment["text"])

        return " ".join(filtered_text)

    def get_keywords(
        self,
        text: str,
        top_k: int = 10
    ) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本内容
            top_k: 返回的关键词数量

        Returns:
            关键词列表
        """
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(text, topK=top_k)
            return keywords
        except ImportError:
            logger.warning("jieba not installed, keyword extraction disabled")
            # 简单的关键词提取：按空格分词，去除常见词
            words = text.split()
            # 这里可以添加停用词过滤
            return words[:top_k]


# 全局实例（延迟加载）
_audio_extractor_instance = None


def get_audio_extractor(model_name: str = "base") -> AudioExtractor:
    """
    获取音频提取器实例（单例模式）

    Args:
        model_name: 模型名称

    Returns:
        AudioExtractor 实例
    """
    global _audio_extractor_instance
    if _audio_extractor_instance is None:
        _audio_extractor_instance = AudioExtractor(model_name)
    return _audio_extractor_instance
