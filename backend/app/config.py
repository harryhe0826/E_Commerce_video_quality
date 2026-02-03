"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用设置"""

    # 应用信息
    APP_NAME: str = "Video Quality Analyzer"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # 路径配置
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"

    # AI 平台配置
    AI_PLATFORM: str = "claude"  # 可选: claude, aihubmix, openai

    # Claude API
    ANTHROPIC_API_KEY: str = ""

    # Aihubmix / OpenAI 兼容平台
    AIHUBMIX_API_KEY: str = ""
    AIHUBMIX_BASE_URL: str = "https://aihubmix.com/v1"
    AIHUBMIX_MODEL: str = "gpt-4o"  # 支持: gpt-4o, claude-3-5-sonnet, gemini-pro 等

    # OpenAI (如果直接使用 OpenAI)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # 数据库
    DATABASE_URL: str = "sqlite:///./video_quality.db"

    # Cloudflare R2 对象存储配置
    USE_R2_STORAGE: bool = False  # 是否使用 R2 存储
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "video-quality-uploads"
    R2_PUBLIC_URL: str = ""  # R2 公共访问域名（如果配置了 custom domain）

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 前端
    FRONTEND_URL: str = "http://localhost:5173"

    # 视频处理配置
    MAX_VIDEO_SIZE_MB: int = 100
    SUPPORTED_FORMATS: str = "mp4,mov,avi"  # 逗号分隔

    @property
    def supported_formats_list(self) -> List[str]:
        """获取支持的格式列表"""
        return self.SUPPORTED_FORMATS.split(',')

    # 模型配置
    WHISPER_MODEL: str = "base"
    YOLO_MODEL: str = "yolov8n.pt"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
