"""
视频相关的 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    video_id: str
    filename: str
    file_path: str
    file_size: int
    status: str
    message: str


class VideoInfo(BaseModel):
    """视频信息"""
    id: str
    filename: str
    file_path: str
    duration: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """视频列表响应"""
    total: int
    videos: list[VideoInfo]
