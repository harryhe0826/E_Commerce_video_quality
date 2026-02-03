"""
剪辑节奏分析器 - 分析视频的镜头切换频率
"""
from typing import Dict, List, Tuple
from loguru import logger


class CutFrequencyAnalyzer:
    """剪辑节奏分析器"""

    def __init__(self):
        # 理想的平均镜头长度范围（秒）
        self.ideal_asl_min = 1.5
        self.ideal_asl_max = 3.0

        # 拖沓镜头阈值（秒）
        self.slow_shot_threshold = 5.0

    def analyze(
        self,
        scenes: List[Tuple[float, float]],
        total_duration: float
    ) -> Dict[str, any]:
        """
        分析剪辑节奏

        Args:
            scenes: 场景列表 [(start, end), ...]
            total_duration: 视频总时长

        Returns:
            分析结果字典
        """
        logger.info(f"Analyzing cut frequency for {len(scenes)} scenes")

        if not scenes or len(scenes) == 0:
            return {
                "score": 50,
                "avg_shot_length": 0.0,
                "total_cuts": 0,
                "slow_shots": [],
                "analysis": "无法检测到场景切换"
            }

        # 1. 计算镜头长度
        shot_lengths = [end - start for start, end in scenes]

        # 2. 计算统计数据
        avg_shot_length = sum(shot_lengths) / len(shot_lengths)
        total_cuts = len(scenes) - 1

        # 3. 识别拖沓镜头
        slow_shots = []
        for i, (start, end) in enumerate(scenes):
            duration = end - start
            if duration >= self.slow_shot_threshold:
                slow_shots.append({
                    "shot_number": i + 1,
                    "start": round(start, 1),
                    "duration": round(duration, 1)
                })

        # 4. 评分
        score = self._calculate_score(avg_shot_length, slow_shots)

        # 5. 生成分析文本
        analysis = self._generate_analysis(avg_shot_length, total_cuts, slow_shots)

        # 6. 生成问题列表
        issues = []
        if score < 70:
            if avg_shot_length > self.ideal_asl_max:
                issues.append(f"平均镜头长度过长（{avg_shot_length:.1f}秒），节奏拖沓")
            if len(slow_shots) > 0:
                issues.append(f"检测到{len(slow_shots)}个超长镜头，建议增加剪辑")
            if total_cuts < 5:
                issues.append("镜头切换次数过少，建议增加剪辑密度")

        result = {
            "score": round(score, 1),
            "avg_shot_length": round(avg_shot_length, 2),
            "total_cuts": total_cuts,
            "slow_shots": slow_shots,
            "analysis": analysis,
            "issues": issues
        }

        logger.info(f"Cut frequency: ASL={avg_shot_length:.2f}s, "
                   f"cuts={total_cuts}, slow_shots={len(slow_shots)}, score={score:.1f}")

        return result

    def _calculate_score(
        self,
        avg_shot_length: float,
        slow_shots: List[Dict]
    ) -> float:
        """
        计算评分

        评分规则:
        - 在理想范围内(1.5-3秒): 100分
        - 小于1.5秒: 逐渐降分
        - 大于3秒: 逐渐降分
        - 每个拖沓镜头扣5分
        """
        # 基础评分
        if self.ideal_asl_min <= avg_shot_length <= self.ideal_asl_max:
            base_score = 100
        elif avg_shot_length < self.ideal_asl_min:
            # 太快，可能眼花缭乱
            diff = self.ideal_asl_min - avg_shot_length
            base_score = max(70, 100 - diff * 20)
        else:
            # 太慢，节奏拖沓
            diff = avg_shot_length - self.ideal_asl_max
            base_score = max(50, 100 - diff * 15)

        # 扣除拖沓镜头的分数
        penalty = len(slow_shots) * 5
        final_score = max(0, base_score - penalty)

        return final_score

    def _generate_analysis(
        self,
        avg_shot_length: float,
        total_cuts: int,
        slow_shots: List[Dict]
    ) -> str:
        """生成分析文本"""
        if self.ideal_asl_min <= avg_shot_length <= self.ideal_asl_max:
            pace = "节奏良好"
        elif avg_shot_length < self.ideal_asl_min:
            pace = "节奏偏快"
        else:
            pace = "节奏偏慢"

        analysis = f"{pace}，平均镜头长度{avg_shot_length:.1f}秒，共{total_cuts}次切换"

        if len(slow_shots) > 0:
            analysis += f"，检测到{len(slow_shots)}个超长镜头"

        if avg_shot_length > self.ideal_asl_max:
            analysis += "，建议增加剪辑密度"

        return analysis


def analyze_cut_frequency(
    scenes: List[Tuple[float, float]],
    total_duration: float
) -> Dict[str, any]:
    """
    便捷函数：分析剪辑节奏

    Args:
        scenes: 场景列表
        total_duration: 视频总时长

    Returns:
        分析结果
    """
    analyzer = CutFrequencyAnalyzer()
    return analyzer.analyze(scenes, total_duration)
