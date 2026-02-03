"""
数据库配置和模型定义
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./video_quality.db")

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()


# 视频表
class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    duration = Column(Float)
    resolution = Column(String)
    fps = Column(Integer)
    file_size = Column(Integer)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)


# 分析结果表
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, index=True)
    video_id = Column(String, index=True)
    overall_score = Column(Float)
    grade = Column(String)
    structural_score = Column(Float)
    visual_score = Column(Float)
    structural_metrics = Column(Text)  # JSON 存储
    visual_metrics = Column(Text)      # JSON 存储
    issues = Column(Text)              # JSON 存储
    ai_evaluation = Column(Text)       # JSON 存储
    created_at = Column(DateTime, default=datetime.utcnow)


# 创建所有表
def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")


# 获取数据库会话
def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # 运行此文件可以初始化数据库
    init_db()
