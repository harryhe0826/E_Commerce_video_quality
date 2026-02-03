"""
Claude (Anthropic) 评估器 - 使用 Claude API 进行多模态分析
"""
import base64
import json
import re
from typing import Dict, List
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Claude评估功能不可用。")

from app.integrations.base_evaluator import BaseAIEvaluator


class ClaudeEvaluator(BaseAIEvaluator):
    """Claude AI 评估器"""

    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs
    ):
        """
        初始化 Claude 评估器

        Args:
            api_key: Anthropic API Key
            model: Claude 模型名称
            **kwargs: 其他参数
        """
        self.model = model
        super().__init__(api_key, **kwargs)

    def _initialize_client(self):
        """初始化 Anthropic 客户端"""
        self.client = None

        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic SDK not available")
            return

        if not self.api_key:
            logger.warning("No API key provided for Claude")
            return

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Claude API client initialized with model={self.model}")
        except Exception as e:
            logger.error(f"Error initializing Claude client: {e}")

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
                "summary": "AI 评估功能未启用（Claude 客户端未初始化）",
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }

        logger.info(f"Starting AI evaluation with Claude (model={self.model})")

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
            logger.info(f"Calling Claude API with model {self.model}...")
            message = self.client.messages.create(
                model=self.model,
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
            return self._handle_error(e, "Claude API call failed")

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

    def _parse_response(self, response_text: str) -> Dict:
        """解析 AI 响应"""
        try:
            # 尝试提取 JSON
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

    def is_available(self) -> bool:
        """检查评估器是否可用"""
        return ANTHROPIC_AVAILABLE and self.client is not None
