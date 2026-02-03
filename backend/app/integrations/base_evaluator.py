"""
AI 评估器基类 - 为不同的 AI 平台提供统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from loguru import logger


class BaseAIEvaluator(ABC):
    """AI 评估器抽象基类"""

    def __init__(self, api_key: str = None, **kwargs):
        """
        初始化 AI 评估器

        Args:
            api_key: API 密钥
            **kwargs: 平台特定的额外参数
        """
        self.api_key = api_key
        self.config = kwargs
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        """初始化 API 客户端（由子类实现）"""
        pass

    @abstractmethod
    def evaluate(
        self,
        key_frames: List[str],
        asr_text: str,
        ocr_text: str,
        analysis_results: Dict
    ) -> Dict[str, any]:
        """
        使用 AI 进行综合评估

        Args:
            key_frames: 关键帧图片路径列表（开头、中间、结尾）
            asr_text: 语音文字
            ocr_text: 屏幕文字
            analysis_results: 规则评分结果

        Returns:
            AI 评估结果，格式为:
            {
                "summary": str,          # 综合评价总结
                "strengths": List[str],  # 优势列表
                "weaknesses": List[str], # 劣势列表
                "recommendations": List[str],  # 改进建议列表
                "raw_response": str      # 原始响应（可选）
            }
        """
        pass

    def _build_prompt(
        self,
        asr_text: str,
        ocr_text: str,
        analysis_results: Dict
    ) -> str:
        """
        构建 AI 评估的 Prompt（可被子类重写）

        Args:
            asr_text: 语音文字
            ocr_text: 屏幕文字
            analysis_results: 分析结果

        Returns:
            格式化的 prompt 字符串
        """
        structural = analysis_results["dimensions"]["structural"]
        visual = analysis_results["dimensions"]["visual"]

        prompt = f"""你是专业的短视频质量分析专家。请分析这个带货短视频的质量。

上面提供了3张关键帧图像（开头、中间、结尾），请结合以下数据进行综合评估：

## 视频文本内容
**语音文字**: {asr_text[:500] if asr_text else "（未检测到语音）"}
**屏幕文字**: {ocr_text[:200] if ocr_text else "（未检测到文字）"}

## 自动化评分结果

### 结构化分析（{structural['score']}分）
- **黄金3秒**: {structural['hook']['score']}分
  - 检测到: {structural['hook']['detected']}
  - 类型: {structural['hook']['hook_type']}
  - 内容: {structural['hook']['content']}

- **CTA检测**: {structural['cta']['score']}分
  - 检测到: {structural['cta']['detected']}
  - 类型: {structural['cta']['cta_type']}

### 视觉动力学（{visual['score']}分）
- **剪辑节奏**: {visual['cut_frequency']['score']}分
  - 平均镜头长度: {visual['cut_frequency']['avg_shot_length']}秒
  - 切换次数: {visual['cut_frequency']['total_cuts']}次

- **视觉重心**: {visual['saliency']['score']}分
  - 产品占比: {visual['saliency']['avg_product_area']:.1%}
  - 中心度: {visual['saliency']['center_ratio']:.2f}

## 请提供

1. **综合评价总结**（2-3句话）
2. **优势**（列出2-3个最突出的优点）
3. **劣势**（列出2-3个最需要改进的问题）
4. **改进建议**（给出3-5条具体、可执行的优化建议）

请以JSON格式返回：
{{
  "summary": "综合评价...",
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["问题1", "问题2"],
  "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
        return prompt

    def _handle_error(self, error: Exception, context: str = "") -> Dict:
        """
        统一的错误处理

        Args:
            error: 异常对象
            context: 错误上下文描述

        Returns:
            错误响应字典
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        logger.error(f"AI evaluation error - {error_msg}")

        return {
            "summary": f"AI 评估出错: {error_msg}",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "raw_response": str(error)
        }

    def is_available(self) -> bool:
        """
        检查评估器是否可用

        Returns:
            True if available, False otherwise
        """
        return self.api_key is not None
