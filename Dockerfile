# 使用官方 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend /app/backend
COPY start.sh /app/start.sh

# 赋予执行权限
RUN chmod +x /app/start.sh

# 创建必要的目录
RUN mkdir -p /app/uploads /app/temp /app/logs

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["/app/start.sh"]
