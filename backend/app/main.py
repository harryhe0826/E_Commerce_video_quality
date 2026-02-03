"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import os

# 创建 FastAPI 应用
app = FastAPI(
    title="Video Quality Analyzer API",
    description="带货短视频质量评估系统 API",
    version="1.0.0"
)

# 配置 CORS
# 从环境变量获取允许的源，默认允许所有来源
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    allowed_origins = ["*"]
    allow_credentials = False  # 使用通配符时不能启用credentials
else:
    allowed_origins = allowed_origins_str.split(",")
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务（用于访问上传的视频）
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 配置日志
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "带货短视频质量评估系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


# 导入路由
from app.api import videos, analysis
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


if __name__ == "__main__":
    import uvicorn

    # 确保必要的目录存在
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
