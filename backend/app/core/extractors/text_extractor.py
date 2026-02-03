"""
文本提取器 - 使用 PaddleOCR 进行文字识别
"""
import os
from typing import List, Dict, Tuple
from loguru import logger

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not installed. OCR功能不可用。")


class TextExtractor:
    """文本提取器（OCR）"""

    def __init__(self, lang: str = "ch"):
        """
        初始化文本提取器

        Args:
            lang: 语言代码 (ch=中文, en=英文)
        """
        self.lang = lang
        self.ocr = None

        if PADDLEOCR_AVAILABLE:
            try:
                logger.info(f"Loading PaddleOCR model: {lang}")
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=lang,
                    show_log=False
                )
                logger.info("PaddleOCR model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading PaddleOCR model: {e}")
        else:
            logger.warning("PaddleOCR not available, OCR功能将被禁用")

    def extract_from_image(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> List[Dict[str, any]]:
        """
        从图片中提取文字

        Args:
            image_path: 图片路径
            confidence_threshold: 置信度阈值

        Returns:
            文字识别结果列表，每个元素包含: {
                'text': 文字内容,
                'confidence': 置信度,
                'bbox': 边界框坐标
            }
        """
        if not PADDLEOCR_AVAILABLE or self.ocr is None:
            logger.warning("PaddleOCR not available, returning empty result")
            return []

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []

        try:
            # 执行 OCR
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return []

            # 解析结果
            texts = []
            for line in result[0]:
                bbox = line[0]  # 边界框坐标
                text_info = line[1]  # (文字, 置信度)
                text = text_info[0]
                confidence = text_info[1]

                # 过滤低置信度结果
                if confidence >= confidence_threshold:
                    texts.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })

            return texts

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return []

    def extract_from_frames(
        self,
        frame_paths: List[str],
        confidence_threshold: float = 0.5
    ) -> Dict[str, List[Dict]]:
        """
        从多个帧中提取文字

        Args:
            frame_paths: 帧图片路径列表
            confidence_threshold: 置信度阈值

        Returns:
            字典，key 为帧路径，value 为该帧的文字列表
        """
        results = {}

        for frame_path in frame_paths:
            texts = self.extract_from_image(frame_path, confidence_threshold)
            if texts:
                results[frame_path] = texts

        return results

    def get_all_text(
        self,
        frame_paths: List[str],
        deduplicate: bool = True
    ) -> str:
        """
        获取所有帧的文字（合并去重）

        Args:
            frame_paths: 帧图片路径列表
            deduplicate: 是否去重

        Returns:
            合并后的文字
        """
        all_texts = []

        for frame_path in frame_paths:
            texts = self.extract_from_image(frame_path)
            for item in texts:
                all_texts.append(item['text'])

        if deduplicate:
            # 去重并保持顺序
            seen = set()
            unique_texts = []
            for text in all_texts:
                if text not in seen:
                    seen.add(text)
                    unique_texts.append(text)
            all_texts = unique_texts

        return " ".join(all_texts)

    def extract_text_positions(
        self,
        image_path: str
    ) -> List[Tuple[str, Tuple[int, int]]]:
        """
        提取文字及其位置（中心点）

        Args:
            image_path: 图片路径

        Returns:
            (文字, (中心x, 中心y)) 列表
        """
        texts = self.extract_from_image(image_path)

        positions = []
        for item in texts:
            text = item['text']
            bbox = item['bbox']

            # 计算中心点
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            center_x = int(sum(x_coords) / len(x_coords))
            center_y = int(sum(y_coords) / len(y_coords))

            positions.append((text, (center_x, center_y)))

        return positions


# 全局实例（延迟加载）
_text_extractor_instance = None


def get_text_extractor(lang: str = "ch") -> TextExtractor:
    """
    获取文本提取器实例（单例模式）

    Args:
        lang: 语言代码

    Returns:
        TextExtractor 实例
    """
    global _text_extractor_instance
    if _text_extractor_instance is None:
        _text_extractor_instance = TextExtractor(lang)
    return _text_extractor_instance
