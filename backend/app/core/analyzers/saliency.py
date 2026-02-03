"""
视觉重心分析器 - 分析产品在画面中的位置和占比
"""
from typing import Dict, List
from loguru import logger


class SaliencyAnalyzer:
    """视觉重心分析器"""

    def __init__(self):
        # 理想的产品占比范围
        self.ideal_area_min = 0.2  # 20%
        self.ideal_area_max = 0.5  # 50%

        # 模糊度阈值（Laplacian方差）
        self.blur_threshold = 100

    def analyze(
        self,
        product_areas: List[float],
        center_ratios: List[float],
        blur_scores: List[float]
    ) -> Dict[str, any]:
        """
        分析视觉重心

        Args:
            product_areas: 每帧的产品占比列表
            center_ratios: 每帧的中心度列表
            blur_scores: 每帧的清晰度分数列表

        Returns:
            分析结果字典
        """
        logger.info(f"Analyzing saliency for {len(product_areas)} frames")

        if not product_areas or len(product_areas) == 0:
            return {
                "score": 50,
                "avg_product_area": 0.0,
                "center_ratio": 0.0,
                "focus_quality": "unknown",
                "blur_frames": [],
                "analysis": "未能检测到产品"
            }

        # 1. 计算平均值
        avg_product_area = sum(product_areas) / len(product_areas)
        avg_center_ratio = sum(center_ratios) / len(center_ratios) if center_ratios else 0.0
        avg_blur_score = sum(blur_scores) / len(blur_scores) if blur_scores else 0.0

        # 2. 识别模糊帧
        blur_frames = []
        for i, score in enumerate(blur_scores):
            if score < self.blur_threshold:
                blur_frames.append(i)

        # 3. 评分
        area_score = self._calculate_area_score(avg_product_area)
        center_score = avg_center_ratio * 100
        clarity_score = max(0, 100 - (len(blur_frames) / len(blur_scores) * 100)) if blur_scores else 80

        # 综合评分：面积40% + 中心度40% + 清晰度20%
        total_score = (area_score * 0.4 + center_score * 0.4 + clarity_score * 0.2)

        # 4. 判断对焦质量
        focus_quality = self._determine_focus_quality(clarity_score)

        # 5. 生成分析文本
        analysis = self._generate_analysis(
            avg_product_area,
            avg_center_ratio,
            len(blur_frames),
            len(blur_scores)
        )

        # 6. 生成问题列表
        issues = []
        if avg_product_area < self.ideal_area_min:
            issues.append(f"产品在画面中过小（{avg_product_area*100:.1f}%），建议增大产品占比")
        elif avg_product_area > self.ideal_area_max:
            issues.append(f"产品占比过大（{avg_product_area*100:.1f}%），可能影响整体观感")

        if avg_center_ratio < 0.6:
            issues.append("产品位置偏离中心，建议调整构图")

        if len(blur_frames) > len(blur_scores) * 0.2:
            issues.append(f"{len(blur_frames)}个帧存在模糊问题，建议检查对焦")

        result = {
            "score": round(total_score, 1),
            "avg_product_area": round(avg_product_area, 3),
            "center_ratio": round(avg_center_ratio, 3),
            "focus_quality": focus_quality,
            "blur_frames": blur_frames,
            "area_score": round(area_score, 1),
            "center_score": round(center_score, 1),
            "clarity_score": round(clarity_score, 1),
            "analysis": analysis,
            "issues": issues
        }

        logger.info(f"Saliency: area={avg_product_area:.2f}, "
                   f"center={avg_center_ratio:.2f}, score={total_score:.1f}")

        return result

    def _calculate_area_score(self, area: float) -> float:
        """
        计算产品占比评分

        评分规则:
        - 在理想范围内(20%-50%): 100分
        - 小于20%: 按比例降分
        - 大于50%: 轻微降分
        """
        if self.ideal_area_min <= area <= self.ideal_area_max:
            return 100.0
        elif area < self.ideal_area_min:
            # 产品过小
            ratio = area / self.ideal_area_min
            return max(50, ratio * 100)
        else:
            # 产品过大（影响较小）
            excess = area - self.ideal_area_max
            return max(70, 100 - excess * 100)

    def _determine_focus_quality(self, clarity_score: float) -> str:
        """判断对焦质量"""
        if clarity_score >= 90:
            return "excellent"
        elif clarity_score >= 70:
            return "good"
        elif clarity_score >= 50:
            return "fair"
        else:
            return "poor"

    def _generate_analysis(
        self,
        area: float,
        center: float,
        blur_count: int,
        total_frames: int
    ) -> str:
        """生成分析文本"""
        parts = []

        # 产品占比
        if self.ideal_area_min <= area <= self.ideal_area_max:
            parts.append(f"产品占比适中（{area*100:.1f}%）")
        elif area < self.ideal_area_min:
            parts.append(f"产品偏小（{area*100:.1f}%）")
        else:
            parts.append(f"产品占比较大（{area*100:.1f}%）")

        # 中心度
        if center >= 0.7:
            parts.append("位置居中")
        else:
            parts.append("位置偏离中心")

        # 清晰度
        if blur_count == 0:
            parts.append("画面清晰")
        elif blur_count <= total_frames * 0.1:
            parts.append("整体清晰")
        else:
            parts.append(f"存在{blur_count}帧模糊")

        return "，".join(parts)


def analyze_saliency(
    product_areas: List[float],
    center_ratios: List[float],
    blur_scores: List[float]
) -> Dict[str, any]:
    """
    便捷函数：分析视觉重心

    Args:
        product_areas: 产品占比列表
        center_ratios: 中心度列表
        blur_scores: 清晰度列表

    Returns:
        分析结果
    """
    analyzer = SaliencyAnalyzer()
    return analyzer.analyze(product_areas, center_ratios, blur_scores)
