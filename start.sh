#!/bin/bash

# 进入后端目录
cd backend

# 创建必要的目录
mkdir -p uploads temp logs

# 启动服务器
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
