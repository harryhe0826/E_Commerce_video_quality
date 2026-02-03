"""
AI 评估器 - 使用 Claude API 进行多模态分析
"""
import os
import base64
import json
from typing import Dict, List
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. AI评估功能不可用。")


class AIEvaluator:
    """AI 评估器"""

    def __init__(self, api_key: str = None):
        """
        初始化 AI 评估器

        Args:
            api_key: Anthropic API Key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude API client initialized")
            except Exception as e:
                logger.error(f"Error initializing Claude client: {e}")
        else:
            logger.warning("Claude API not available, AI评估功能将被禁用")

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
            AI 评估结果
        """
        if not self.client:
            logger.warning("Claude API not available, returning empty result")
            return {
                "summary": "AI 评估功能未启用",
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }

        logger.info("Starting AI evaluation with Claude")

        try:
            # 1. 编码图片
            encoded_frames = self._encode_frames(key_frames)

            # 2. 构建 Prompt
            prompt = self._build_prompt(asr_text, ocr_text, analysis_results)

            # 3. 构建消息内容
            content = []

            # 添加图片
            for i, encoded_frame in enumerate(encoded_frames):
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encoded_frame
                    }
                })

            # 添加文本
            content.append({
                "type": "text",
                "text": prompt
            })

            # 4. 调用 Claude API
            logger.info("Calling Claude API...")
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # 5. 解析响应
            response_text = message.content[0].text
            result = self._parse_response(response_text)

            logger.info("AI evaluation completed successfully")

            return result

        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return {
                "summary": f"AI 评估出错: {str(e)}",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "raw_response": str(e)
            }

    def _encode_frames(self, frame_paths: List[str]) -> List[str]:
        """将图片编码为 Base64"""
        encoded_frames = []

        for path in frame_paths[:3]:  # 最多3张图片
            try:
                with open(path, 'rb') as f:
                    image_data = f.read()
                    encoded = base64.b64encode(image_data).decode('utf-8')
                    encoded_frames.append(encoded)
            except Exception as e:
                logger.error(f"Error encoding frame {path}: {e}")

        return encoded_frames

    def _build_prompt(
        self,
        asr_text: str,
        ocr_text: str,
        analysis_results: Dict
    ) -> str:
        """构建 AI 评估的 Prompt"""
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

    def _parse_response(self, response_text: str) -> Dict:
        """解析 AI 响应"""
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

            if json_match:
                result = json.loads(json_match.group())
                return {
                    "summary": result.get("summary", ""),
                    "strengths": result.get("strengths", []),
                    "weaknesses": result.get("weaknesses", []),
                    "recommendations": result.get("recommendations", []),
                    "raw_response": response_text
                }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")

        # 如果解析失败，返回原始文本
        return {
            "summary": response_text[:200],
            "strengths": ["详见完整响应"],
            "weaknesses": ["详见完整响应"],
            "recommendations": ["详见完整响应"],
            "raw_response": response_text
        }


def evaluate_with_ai(
    key_frames: List[str],
    asr_text: str,
    ocr_text: str,
    analysis_results: Dict,
    api_key: str = None
) -> Dict:
    """
    便捷函数：使用 AI 评估

    Args:
        key_frames: 关键帧列表
        asr_text: 语音文字
        ocr_text: 屏幕文字
        analysis_results: 分析结果
        api_key: API Key

    Returns:
        AI 评估结果
    """
    evaluator = AIEvaluator(api_key)
    return evaluator.evaluate(key_frames, asr_text, ocr_text, analysis_results)
