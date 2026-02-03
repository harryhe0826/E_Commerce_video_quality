"""
CTA 检测器 - 检测视频结尾的行动指令
"""
from typing import Dict, List
from loguru import logger


class CTADetector:
    """CTA（Call To Action）检测器"""

    def __init__(self):
        # 中文 CTA 关键词
        self.cta_keywords_cn = [
            "点击", "购买", "下单", "立即", "马上",
            "抢购", "秒杀", "优惠", "折扣", "领取",
            "关注", "评论", "转发", "分享", "收藏"
        ]

        # 英文 CTA 关键词
        self.cta_keywords_en = [
            "click", "buy", "shop", "order", "get",
            "link", "bio", "now", "today", "limited"
        ]

        # 所有关键词
        self.cta_keywords = self.cta_keywords_cn + self.cta_keywords_en

    def analyze(
        self,
        asr_text: str,
        ocr_text: str,
        duration: float,
        has_button: bool = False
    ) -> Dict[str, any]:
        """
        分析 CTA

        Args:
            asr_text: 最后5秒的语音文字
            ocr_text: 最后5秒的屏幕文字
            duration: 视频总时长
            has_button: 是否检测到按钮图标

        Returns:
            分析结果字典
        """
        logger.info("Analyzing CTA (Call To Action)")

        # 1. 文本检测
        asr_has_cta, asr_keywords = self._check_cta_keywords(asr_text)
        ocr_has_cta, ocr_keywords = self._check_cta_keywords(ocr_text)

        # 2. 视觉检测（按钮）
        visual_cta = has_button

        # 3. 综合判断
        detected = asr_has_cta or ocr_has_cta or visual_cta

        # 4. 确定 CTA 类型
        if asr_has_cta:
            cta_type = "audio"
        elif visual_cta:
            cta_type = "visual"
        elif ocr_has_cta:
            cta_type = "text"
        else:
            cta_type = "none"

        # 5. 评分
        score = 100 if detected else 0

        # 6. 提取内容
        content = self._extract_content(
            asr_text, ocr_text,
            asr_keywords, ocr_keywords
        )

        # 7. 生成问题列表
        issues = []
        if not detected:
            issues.append("视频结尾缺少明确的行动指令（CTA）")
            issues.append("建议添加：点击购买、关注账号等引导语")

        # 8. 计算时间戳（最后5秒的开始时间）
        timestamp = max(0, duration - 5)

        result = {
            "score": score,
            "detected": detected,
            "cta_type": cta_type,
            "content": content,
            "timestamp": round(timestamp, 1),
            "has_audio_cta": asr_has_cta,
            "has_visual_cta": visual_cta,
            "has_text_cta": ocr_has_cta,
            "keywords_found": list(set(asr_keywords + ocr_keywords)),
            "issues": issues
        }

        logger.info(f"CTA analysis: score={score}, detected={detected}, type={cta_type}")

        return result

    def _check_cta_keywords(self, text: str) -> tuple[bool, List[str]]:
        """
        检查文本中是否包含 CTA 关键词

        Returns:
            (是否包含, 找到的关键词列表)
        """
        found_keywords = []
        for keyword in self.cta_keywords:
            if keyword in text.lower():
                found_keywords.append(keyword)

        has_cta = len(found_keywords) > 0
        return has_cta, found_keywords

    def _extract_content(
        self,
        asr_text: str,
        ocr_text: str,
        asr_keywords: List[str],
        ocr_keywords: List[str]
    ) -> str:
        """提取 CTA 内容片段"""
        # 优先返回包含关键词的文本
        if asr_keywords and asr_text:
            return asr_text[:50]
        elif ocr_keywords and ocr_text:
            return ocr_text[:50]
        else:
            return "（未检测到行动指令）"


def analyze_cta(
    asr_text: str,
    ocr_text: str,
    duration: float,
    has_button: bool = False
) -> Dict[str, any]:
    """
    便捷函数：分析 CTA

    Args:
        asr_text: 最后5秒的语音文字
        ocr_text: 最后5秒的屏幕文字
        duration: 视频总时长
        has_button: 是否检测到按钮

    Returns:
        分析结果
    """
    detector = CTADetector()
    return detector.analyze(asr_text, ocr_text, duration, has_button)
