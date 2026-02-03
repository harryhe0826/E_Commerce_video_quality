"""
Aihubmix 评估器 - 支持 OpenAI 兼容 API 的第三方平台
"""
import base64
import json
import re
from typing import Dict, List
from loguru import logger

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK not installed. Aihubmix评估功能不可用。")

from app.integrations.base_evaluator import BaseAIEvaluator


class AihubmixEvaluator(BaseAIEvaluator):
    """
    Aihubmix AI 评估器

    支持所有 OpenAI 兼容的第三方大模型聚合平台，如：
    - Aihubmix
    - new-api
    - one-api
    等使用 OpenAI API 格式的平台
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://aihubmix.com/v1",
        model: str = "gpt-4o",
        **kwargs
    ):
        """
        初始化 Aihubmix 评估器

        Args:
            api_key: API 密钥
            base_url: API 基础URL（默认为 aihubmix.com，也可以是其他兼容平台）
            model: 模型名称（默认 gpt-4o，支持 Claude、Gemini、Qwen 等）
            **kwargs: 其他参数
        """
        self.base_url = base_url
        self.model = model
        super().__init__(api_key, **kwargs)

    def _initialize_client(self):
        """初始化 OpenAI 客户端"""
        self.client = None

        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI SDK not available")
            return

        if not self.api_key:
            logger.warning("No API key provided for Aihubmix")
            return

        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"Aihubmix client initialized with base_url={self.base_url}, model={self.model}")
        except Exception as e:
            logger.error(f"Error initializing Aihubmix client: {e}")

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
            logger.warning("Aihubmix client not available, returning empty result")
            return {
                "summary": "AI 评估功能未启用（Aihubmix 客户端未初始化）",
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }

        logger.info(f"Starting AI evaluation with Aihubmix (model={self.model})")

        try:
            # 1. 编码图片
            encoded_frames = self._encode_frames(key_frames)

            # 2. 构建 Prompt
            prompt = self._build_prompt(asr_text, ocr_text, analysis_results)

            # 3. 构建消息内容（OpenAI Vision API 格式）
            content = []

            # 添加图片
            for i, encoded_frame in enumerate(encoded_frames):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_frame}",
                        "detail": "auto"
                    }
                })

            # 添加文本
            content.append({
                "type": "text",
                "text": prompt
            })

            # 4. 调用 API
            logger.info(f"Calling Aihubmix API with model {self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=2000,
                temperature=1.0
            )

            # 5. 解析响应
            response_text = response.choices[0].message.content
            result = self._parse_response(response_text)

            logger.info("AI evaluation completed successfully")

            return result

        except Exception as e:
            return self._handle_error(e, "Aihubmix API call failed")

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
        return OPENAI_AVAILABLE and self.client is not None
