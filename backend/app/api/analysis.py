"""
分析相关的 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.db import get_db, Video, AnalysisResult
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/start/{video_id}")
async def start_analysis(
    video_id: str,
    use_ai: bool = True,
    x_ai_api_key: Optional[str] = Header(None, alias="x-ai-api-key"),
    x_ai_platform: Optional[str] = Header(None, alias="x-ai-platform"),
    x_ai_model: Optional[str] = Header(None, alias="x-ai-model"),
    x_ai_base_url: Optional[str] = Header(None, alias="x-ai-base-url"),
    # 保留旧的 Claude 专用 header 以向后兼容
    x_claude_api_key: Optional[str] = Header(None, alias="x-claude-api-key"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    开始分析视频

    Args:
        video_id: 视频 ID
        use_ai: 是否使用 AI 评估
        x_ai_api_key: AI API Key (可选，从请求头获取)
        x_ai_platform: AI 平台 (claude, aihubmix, openai 等，可选)
        x_ai_model: AI 模型名称 (可选)
        x_ai_base_url: API 基础 URL (可选，用于第三方平台)
        x_claude_api_key: Claude API Key (保留以向后兼容，可选)
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        分析任务信息
    """
    try:
        # 检查视频是否存在
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")

        # 检查是否已经有分析结果
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.video_id == video_id
        ).first()

        if existing_result:
            return {
                "message": "该视频已有分析结果",
                "result_id": existing_result.id,
                "status": "completed"
            }

        # 创建分析服务
        analysis_service = AnalysisService(db)

        # 确定使用的 API Key（优先使用新的通用 header，否则使用旧的 Claude header）
        api_key = x_ai_api_key or x_claude_api_key

        # 如果使用了旧的 Claude header 但没有指定平台，则默认使用 Claude
        platform = x_ai_platform
        if x_claude_api_key and not platform:
            platform = "claude"

        # 同步执行分析（MVP版本）
        logger.info(f"Starting analysis for video: {video_id}")
        result = analysis_service.analyze_video(
            video_id,
            use_ai=use_ai,
            api_key=api_key,
            ai_platform=platform,
            ai_model=x_ai_model,
            ai_base_url=x_ai_base_url
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "message": "分析完成",
            "result_id": result["result_id"],
            "status": "completed",
            "video_id": video_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/result/{result_id}")
async def get_analysis_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """
    获取分析结果

    Args:
        result_id: 结果 ID
        db: 数据库会话

    Returns:
        分析结果
    """
    analysis_service = AnalysisService(db)
    result = analysis_service.get_result(result_id)

    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")

    return result


@router.get("/result/by-video/{video_id}")
async def get_result_by_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """
    根据视频ID获取分析结果

    Args:
        video_id: 视频 ID
        db: 数据库会话

    Returns:
        分析结果
    """
    result = db.query(AnalysisResult).filter(
        AnalysisResult.video_id == video_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="该视频没有分析结果")

    analysis_service = AnalysisService(db)
    return analysis_service.get_result(result.id)


@router.get("/list")
async def get_analysis_list(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取分析结果列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话

    Returns:
        分析结果列表
    """
    total = db.query(AnalysisResult).count()
    results = (
        db.query(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "results": [
            {
                "id": r.id,
                "video_id": r.video_id,
                "overall_score": r.overall_score,
                "grade": r.grade,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]
    }
