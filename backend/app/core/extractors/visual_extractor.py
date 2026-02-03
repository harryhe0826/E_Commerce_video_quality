"""
视觉特征提取器 - 使用 YOLOv8 和 OpenCV 进行图像分析
"""
import os
from typing import List, Dict, Tuple
from loguru import logger
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not installed. 视觉分析功能不可用。")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("Ultralytics (YOLOv8) not installed. 对象检测功能不可用。")


class VisualExtractor:
    """视觉特征提取器"""

    def __init__(self, model_name: str = "yolov8n.pt"):
        """
        初始化视觉提取器

        Args:
            model_name: YOLO 模型名称
        """
        self.model_name = model_name
        self.model = None

        if YOLO_AVAILABLE:
            try:
                logger.info(f"Loading YOLO model: {model_name}")
                self.model = YOLO(model_name)
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
        else:
            logger.warning("YOLOv8 not available, 对象检测功能将被禁用")

    def detect_objects(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> List[Dict[str, any]]:
        """
        检测图片中的对象

        Args:
            image_path: 图片路径
            confidence_threshold: 置信度阈值

        Returns:
            对象列表，每个元素包含类别、置信度、边界框等
        """
        if not YOLO_AVAILABLE or self.model is None:
            logger.warning("YOLO not available, returning empty result")
            return []

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []

        try:
            # 运行检测
            results = self.model(image_path, verbose=False)

            # 解析结果
            objects = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    confidence = float(box.conf[0])

                    if confidence >= confidence_threshold:
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].tolist()

                        # 获取类别
                        cls_id = int(box.cls[0])
                        cls_name = result.names[cls_id]

                        # 计算面积
                        area = (x2 - x1) * (y2 - y1)

                        objects.append({
                            'class': cls_name,
                            'confidence': confidence,
                            'bbox': [x1, y1, x2, y2],
                            'area': area,
                            'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                        })

            return objects

        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
            return []

    def analyze_saturation(
        self,
        image_path: str
    ) -> float:
        """
        分析图片的色彩饱和度

        Args:
            image_path: 图片路径

        Returns:
            平均饱和度 (0-255)
        """
        if not OPENCV_AVAILABLE:
            return 0.0

        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                return 0.0

            # 转换为 HSV 色彩空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # 提取饱和度通道 (S)
            saturation = hsv[:, :, 1]

            # 计算平均饱和度
            avg_saturation = np.mean(saturation)

            return float(avg_saturation)

        except Exception as e:
            logger.error(f"Error analyzing saturation: {e}")
            return 0.0

    def calculate_blur_score(
        self,
        image_path: str
    ) -> float:
        """
        计算图片的模糊度（Laplacian 方差）

        Args:
            image_path: 图片路径

        Returns:
            模糊度分数（越大越清晰）
        """
        if not OPENCV_AVAILABLE:
            return 0.0

        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                return 0.0

            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 计算 Laplacian 方差
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            return float(laplacian_var)

        except Exception as e:
            logger.error(f"Error calculating blur score: {e}")
            return 0.0

    def calculate_product_metrics(
        self,
        image_path: str,
        target_classes: List[str] = None
    ) -> Dict[str, any]:
        """
        计算产品相关的指标

        Args:
            image_path: 图片路径
            target_classes: 目标产品类别（如果为 None，使用所有检测到的对象）

        Returns:
            产品指标字典
        """
        if not OPENCV_AVAILABLE:
            return {}

        try:
            # 读取图片获取尺寸
            image = cv2.imread(image_path)
            if image is None:
                return {}

            h, w = image.shape[:2]
            image_area = h * w

            # 检测对象
            objects = self.detect_objects(image_path)

            if not objects:
                return {
                    'product_area_ratio': 0.0,
                    'center_ratio': 0.0,
                    'products_found': 0
                }

            # 筛选目标类别
            if target_classes:
                objects = [obj for obj in objects if obj['class'] in target_classes]

            if not objects:
                return {
                    'product_area_ratio': 0.0,
                    'center_ratio': 0.0,
                    'products_found': 0
                }

            # 选择最大的对象作为主产品
            main_product = max(objects, key=lambda x: x['area'])

            # 计算产品占比
            product_area_ratio = main_product['area'] / image_area

            # 计算产品中心度
            product_center_x, product_center_y = main_product['center']
            image_center_x, image_center_y = w / 2, h / 2

            # 计算距离中心的距离比例
            distance = np.sqrt(
                (product_center_x - image_center_x) ** 2 +
                (product_center_y - image_center_y) ** 2
            )
            max_distance = np.sqrt((w / 2) ** 2 + (h / 2) ** 2)
            center_ratio = 1 - (distance / max_distance)

            return {
                'product_area_ratio': float(product_area_ratio),
                'center_ratio': float(center_ratio),
                'products_found': len(objects),
                'main_product': main_product
            }

        except Exception as e:
            logger.error(f"Error calculating product metrics: {e}")
            return {}

    def analyze_frames(
        self,
        frame_paths: List[str]
    ) -> Dict[str, any]:
        """
        分析多个帧的视觉特征

        Args:
            frame_paths: 帧图片路径列表

        Returns:
            聚合的视觉特征
        """
        saturation_values = []
        blur_scores = []
        product_area_ratios = []
        center_ratios = []

        for frame_path in frame_paths:
            # 饱和度
            saturation = self.analyze_saturation(frame_path)
            if saturation > 0:
                saturation_values.append(saturation)

            # 清晰度
            blur_score = self.calculate_blur_score(frame_path)
            if blur_score > 0:
                blur_scores.append(blur_score)

            # 产品指标
            product_metrics = self.calculate_product_metrics(frame_path)
            if product_metrics:
                product_area_ratios.append(product_metrics['product_area_ratio'])
                center_ratios.append(product_metrics['center_ratio'])

        return {
            'avg_saturation': np.mean(saturation_values) if saturation_values else 0.0,
            'avg_blur_score': np.mean(blur_scores) if blur_scores else 0.0,
            'avg_product_area': np.mean(product_area_ratios) if product_area_ratios else 0.0,
            'avg_center_ratio': np.mean(center_ratios) if center_ratios else 0.0,
            'blur_frames': [i for i, score in enumerate(blur_scores) if score < 100]
        }


# 全局实例（延迟加载）
_visual_extractor_instance = None


def get_visual_extractor(model_name: str = "yolov8n.pt") -> VisualExtractor:
    """
    获取视觉提取器实例（单例模式）

    Args:
        model_name: 模型名称

    Returns:
        VisualExtractor 实例
    """
    global _visual_extractor_instance
    if _visual_extractor_instance is None:
        _visual_extractor_instance = VisualExtractor(model_name)
    return _visual_extractor_instance
