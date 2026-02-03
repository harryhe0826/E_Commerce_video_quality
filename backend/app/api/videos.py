"""
视频相关的 API 路由
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from app.db import get_db
from app.models.video import VideoUploadResponse, VideoInfo, VideoListResponse
from app.services.video_service import VideoService

router = APIRouter()


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传视频文件

    Args:
        file: 上传的视频文件
        db: 数据库会话

    Returns:
        上传结果
    """
    try:
        # 读取文件内容
        logger.info(f"Uploading video: {file.filename}")
        content = await file.read()

        # 创建视频服务
        video_service = VideoService(db)

        # 保存文件
        video_id, file_path = video_service.save_uploaded_video(
            content,
            file.filename
        )

        # 处理视频
        result = video_service.process_video(video_id, file_path, file.filename)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        video = result['video']

        return VideoUploadResponse(
            video_id=video.id,
            filename=video.filename,
            file_path=video.file_path,
            file_size=video.file_size,
            status=video.status,
            message="视频上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/{video_id}", response_model=VideoInfo)
async def get_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    获取视频信息

    Args:
        video_id: 视频 ID
        db: 数据库会话

    Returns:
        视频信息
    """
    video_service = VideoService(db)
    video = video_service.get_video(video_id)

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    return video


@router.get("/", response_model=VideoListResponse)
async def get_video_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取视频列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话

    Returns:
        视频列表
    """
    video_service = VideoService(db)
    videos, total = video_service.get_video_list(skip, limit)

    return VideoListResponse(
        total=total,
        videos=videos
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    删除视频

    Args:
        video_id: 视频 ID
        db: 数据库会话

    Returns:
        删除结果
    """
    video_service = VideoService(db)
    success = video_service.delete_video(video_id)

    if not success:
        raise HTTPException(status_code=404, detail="视频不存在或删除失败")

    return {"message": "视频删除成功"}
