"""
黄金3秒检测器 - 分析视频开头的吸引力
"""
import re
from typing import Dict, List
from loguru import logger


class HookDetector:
    """黄金3秒检测器"""

    def __init__(self):
        # 冲突感词汇
        self.conflict_words = [
            "竟然", "没想到", "震惊", "你知道吗", "不要买",
            "千万别", "绝对不能", "必须", "警惕", "揭秘"
        ]

        # 疑问句模式
        self.question_patterns = [
            r'.*[吗?？]$',
            r'^为什么.*',
            r'^怎么.*',
            r'^如何.*',
            r'^什么.*',
        ]

    def analyze(
        self,
        asr_text: str,
        ocr_text: str,
        saturation_changes: float = 0.0
    ) -> Dict[str, any]:
        """
        分析黄金3秒

        Args:
            asr_text: 前3秒的语音文字
            ocr_text: 前3秒的屏幕文字
            saturation_changes: 色彩饱和度变化幅度

        Returns:
            分析结果字典
        """
        logger.info("Analyzing hook (first 3 seconds)")

        # 1. 文本分析
        has_conflict = self._check_conflict_words(asr_text, ocr_text)
        has_question = self._check_question_patterns(asr_text)

        # 文本评分：有冲突感或疑问句得高分
        if has_conflict or has_question:
            text_score = 50
            hook_type = "conflict" if has_conflict else "question"
        else:
            text_score = 20
            hook_type = "visual"

        # 2. 视觉变化分析
        # 饱和度变化越大，视觉冲击力越强
        visual_score = min(50, saturation_changes * 20)

        # 3. 总分
        total_score = text_score + visual_score

        # 4. 判定是否有效
        detected = total_score > 60

        # 5. 提取内容片段
        content = self._extract_content(asr_text, ocr_text)

        # 6. 生成问题列表
        issues = []
        if not detected:
            if text_score < 30:
                issues.append("开头文案缺乏冲击力，建议使用疑问句或冲突感词汇")
            if visual_score < 30:
                issues.append("开头画面变化不够，建议增加视觉冲击")

        result = {
            "score": round(total_score, 1),
            "detected": detected,
            "hook_type": hook_type,
            "content": content,
            "has_conflict": has_conflict,
            "has_question": has_question,
            "saturation_change": round(saturation_changes, 2),
            "text_score": text_score,
            "visual_score": round(visual_score, 1),
            "issues": issues
        }

        logger.info(f"Hook analysis: score={total_score:.1f}, detected={detected}, type={hook_type}")

        return result

    def _check_conflict_words(self, asr_text: str, ocr_text: str) -> bool:
        """检查是否包含冲突感词汇"""
        combined_text = asr_text + " " + ocr_text
        return any(word in combined_text for word in self.conflict_words)

    def _check_question_patterns(self, text: str) -> bool:
        """检查是否是疑问句"""
        return any(re.match(pattern, text.strip()) for pattern in self.question_patterns)

    def _extract_content(self, asr_text: str, ocr_text: str) -> str:
        """提取内容片段（用于展示）"""
        # 优先使用 ASR，因为它通常更完整
        if asr_text and len(asr_text) > 5:
            return asr_text[:50]
        elif ocr_text and len(ocr_text) > 5:
            return ocr_text[:50]
        else:
            return "（未检测到文字内容）"


def analyze_hook(
    asr_text: str,
    ocr_text: str,
    saturation_changes: float = 0.0
) -> Dict[str, any]:
    """
    便捷函数：分析黄金3秒

    Args:
        asr_text: 前3秒的语音文字
        ocr_text: 前3秒的屏幕文字
        saturation_changes: 色彩饱和度变化幅度

    Returns:
        分析结果
    """
    detector = HookDetector()
    return detector.analyze(asr_text, ocr_text, saturation_changes)
