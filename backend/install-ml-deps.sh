#!/bin/bash
# 安装 ML 依赖库
# 这个过程可能需要 20-40 分钟

echo "=== 开始安装 ML 依赖 ==="
echo "预计时间: 20-40 分钟"
echo ""

# 激活虚拟环境
source venv/bin/activate

echo "1/5 安装 PyTorch (这可能需要 10-15 分钟)..."
pip install torch torchvision torchaudio

echo ""
echo "2/5 安装 OpenAI Whisper..."
pip install openai-whisper

echo ""
echo "3/5 安装 PaddleOCR 和 PaddlePaddle..."
pip install paddlepaddle paddleocr

echo ""
echo "4/5 安装 PySceneDetect..."
pip install scenedetect[opencv]

echo ""
echo "5/5 安装 Ultralytics YOLOv8..."
pip install ultralytics

echo ""
echo "=== 安装完成 ==="
echo ""
echo "接下来需要配置 Claude API Key："
echo "1. 访问 https://console.anthropic.com/"
echo "2. 创建 API Key"
echo "3. 编辑 .env 文件，设置 ANTHROPIC_API_KEY"
