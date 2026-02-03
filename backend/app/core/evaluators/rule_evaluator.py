"""
规则评分器 - 整合各维度分析结果并计算总分
"""
from typing import Dict, List
from loguru import logger


class RuleEvaluator:
    """规则评分器"""

    def __init__(self):
        # 维度权重
        self.weights = {
            "structural": 0.5,  # 结构化分析 50%
            "visual": 0.5       # 视觉动力学 50%
        }

        # 子维度权重
        self.structural_weights = {
            "hook": 0.5,  # 黄金3秒 50%
            "cta": 0.5    # CTA 50%
        }

        self.visual_weights = {
            "cut_frequency": 0.5,  # 剪辑节奏 50%
            "saliency": 0.5        # 视觉重心 50%
        }

    def evaluate(
        self,
        hook_result: Dict,
        cta_result: Dict,
        cut_frequency_result: Dict,
        saliency_result: Dict
    ) -> Dict[str, any]:
        """
        综合评估

        Args:
            hook_result: 黄金3秒检测结果
            cta_result: CTA检测结果
            cut_frequency_result: 剪辑节奏分析结果
            saliency_result: 视觉重心分析结果

        Returns:
            评估结果字典
        """
        logger.info("Evaluating video quality with rule-based scoring")

        # 1. 计算结构化维度得分
        structural_score = (
            hook_result["score"] * self.structural_weights["hook"] +
            cta_result["score"] * self.structural_weights["cta"]
        )

        # 2. 计算视觉维度得分
        visual_score = (
            cut_frequency_result["score"] * self.visual_weights["cut_frequency"] +
            saliency_result["score"] * self.visual_weights["saliency"]
        )

        # 3. 计算总分
        overall_score = (
            structural_score * self.weights["structural"] +
            visual_score * self.weights["visual"]
        )

        # 4. 确定等级
        grade = self._calculate_grade(overall_score)

        # 5. 收集所有问题
        issues = self._collect_issues(
            hook_result, cta_result,
            cut_frequency_result, saliency_result
        )

        # 6. 生成建议
        suggestions = self._generate_suggestions(issues)

        result = {
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "dimensions": {
                "structural": {
                    "score": round(structural_score, 1),
                    "hook": hook_result,
                    "cta": cta_result
                },
                "visual": {
                    "score": round(visual_score, 1),
                    "cut_frequency": cut_frequency_result,
                    "saliency": saliency_result
                }
            },
            "issues": issues,
            "suggestions": suggestions
        }

        logger.info(f"Evaluation complete: overall={overall_score:.1f}, grade={grade}")

        return result

    def _calculate_grade(self, score: float) -> str:
        """根据分数计算等级"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        else:
            return "C"

    def _collect_issues(
        self,
        hook_result: Dict,
        cta_result: Dict,
        cut_frequency_result: Dict,
        saliency_result: Dict
    ) -> List[Dict]:
        """收集所有问题"""
        issues = []

        # 从各个分析器收集问题
        analyzers = [
            ("structural", "hook", hook_result),
            ("structural", "cta", cta_result),
            ("visual", "cut_frequency", cut_frequency_result),
            ("visual", "saliency", saliency_result)
        ]

        for dimension, analyzer_name, result in analyzers:
            if "issues" in result and result["issues"]:
                for issue_text in result["issues"]:
                    # 确定严重程度
                    severity = self._determine_severity(result["score"])

                    issues.append({
                        "dimension": dimension,
                        "analyzer": analyzer_name,
                        "severity": severity,
                        "issue": issue_text,
                        "timestamp": result.get("timestamp"),
                        "score": result["score"]
                    })

        # 按严重程度排序
        severity_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(key=lambda x: severity_order[x["severity"]])

        return issues

    def _determine_severity(self, score: float) -> str:
        """根据分数确定问题严重程度"""
        if score < 50:
            return "high"
        elif score < 70:
            return "medium"
        else:
            return "low"

    def _generate_suggestions(self, issues: List[Dict]) -> List[str]:
        """基于问题生成改进建议"""
        suggestions = []

        # 统计问题类型
        has_hook_issue = any(i["analyzer"] == "hook" for i in issues)
        has_cta_issue = any(i["analyzer"] == "cta" for i in issues)
        has_rhythm_issue = any(i["analyzer"] == "cut_frequency" for i in issues)
        has_visual_issue = any(i["analyzer"] == "saliency" for i in issues)

        # 生成针对性建议
        if has_hook_issue:
            suggestions.append("优化视频开头，使用疑问句或冲突感词汇吸引注意力")

        if has_cta_issue:
            suggestions.append("在视频结尾添加明确的行动指令，引导用户点击或购买")

        if has_rhythm_issue:
            suggestions.append("增加剪辑密度，保持1.5-3秒的镜头长度，维持快节奏")

        if has_visual_issue:
            suggestions.append("调整产品位置和大小，确保产品清晰并处于画面中心")

        # 如果没有具体问题，给出通用建议
        if not suggestions:
            suggestions.append("视频质量整体良好，继续保持当前水平")

        return suggestions


def evaluate_video(
    hook_result: Dict,
    cta_result: Dict,
    cut_frequency_result: Dict,
    saliency_result: Dict
) -> Dict[str, any]:
    """
    便捷函数：评估视频质量

    Args:
        hook_result: 黄金3秒结果
        cta_result: CTA结果
        cut_frequency_result: 剪辑节奏结果
        saliency_result: 视觉重心结果

    Returns:
        评估结果
    """
    evaluator = RuleEvaluator()
    return evaluator.evaluate(
        hook_result, cta_result,
        cut_frequency_result, saliency_result
    )
