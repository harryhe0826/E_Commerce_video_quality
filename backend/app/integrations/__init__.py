"""
AI 评估器集成模块

支持多种 AI 平台：
- Claude (Anthropic)
- Aihubmix (OpenAI 兼容平台)
- 其他 OpenAI 兼容的第三方平台
"""
import os
from typing import Optional
from loguru import logger

from app.integrations.base_evaluator import BaseAIEvaluator
from app.integrations.claude_evaluator import ClaudeEvaluator
from app.integrations.aihubmix_evaluator import AihubmixEvaluator


class EvaluatorFactory:
    """AI 评估器工厂类"""

    # 支持的平台
    SUPPORTED_PLATFORMS = {
        "claude": ClaudeEvaluator,
        "aihubmix": AihubmixEvaluator,
        "openai": AihubmixEvaluator,  # 使用相同的 OpenAI 兼容评估器
    }

    @classmethod
    def create_evaluator(
        cls,
        platform: str = "claude",
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseAIEvaluator:
        """
        创建 AI 评估器实例

        Args:
            platform: AI 平台名称 (claude, aihubmix, openai 等)
            api_key: API 密钥（可选，如果不提供则从环境变量读取）
            **kwargs: 平台特定的额外参数
                - model: 模型名称
                - base_url: API 基础 URL（用于 aihubmix 等平台）

        Returns:
            AI 评估器实例

        Raises:
            ValueError: 如果平台不支持
        """
        platform_lower = platform.lower()

        if platform_lower not in cls.SUPPORTED_PLATFORMS:
            supported = ", ".join(cls.SUPPORTED_PLATFORMS.keys())
            raise ValueError(
                f"Unsupported AI platform: {platform}. "
                f"Supported platforms: {supported}"
            )

        evaluator_class = cls.SUPPORTED_PLATFORMS[platform_lower]

        # 如果没有提供 API key，尝试从环境变量读取
        if not api_key:
            api_key = cls._get_api_key_from_env(platform_lower)

        logger.info(f"Creating {platform} evaluator")

        return evaluator_class(api_key=api_key, **kwargs)

    @staticmethod
    def _get_api_key_from_env(platform: str) -> Optional[str]:
        """
        从环境变量读取 API Key

        Args:
            platform: 平台名称

        Returns:
            API Key 或 None
        """
        # 环境变量映射
        env_key_mapping = {
            "claude": "ANTHROPIC_API_KEY",
            "aihubmix": "AIHUBMIX_API_KEY",
            "openai": "OPENAI_API_KEY",
        }

        env_key = env_key_mapping.get(platform)
        if env_key:
            return os.getenv(env_key)

        return None

    @classmethod
    def list_supported_platforms(cls) -> list:
        """
        列出所有支持的平台

        Returns:
            支持的平台列表
        """
        return list(cls.SUPPORTED_PLATFORMS.keys())


# 导出主要类和函数
__all__ = [
    "BaseAIEvaluator",
    "ClaudeEvaluator",
    "AihubmixEvaluator",
    "EvaluatorFactory",
]
