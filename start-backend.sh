#!/bin/bash

# 启动后端服务器
echo "🚀 启动后端服务器..."
cd backend
source venv/bin/activate
python app/main.py
