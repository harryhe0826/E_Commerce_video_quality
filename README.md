# 带货短视频质量评估系统

基于 AI 的带货短视频质量评估 Web 应用，能够自动分析视频的结构、视觉等多维度特征，并给出专业的评分和改进建议。

## 项目概述

本系统使用 Claude AI 结合多种计算机视觉和音频处理技术，对带货短视频进行全方位质量评估。

### 核心功能

- **视频上传与预处理**: 支持 mp4、mov、avi 格式，自动提取元数据
- **多维度分析**:
  - **结构化分析**: 黄金3秒检测 + CTA（行动召唤）检测
  - **视觉动力学**: 剪辑节奏分析 + 产品视觉重心分析
- **智能评分**: 规则评分 + Claude AI 综合评估
- **详细报告**: 问题清单、优势分析、改进建议

### 技术栈

**后端**:
- FastAPI - Web 框架
- OpenAI Whisper - 语音识别（ASR）
- PaddleOCR - 文字识别（OCR）
- PySceneDetect - 场景检测
- YOLOv8 - 对象检测
- Claude 3.5 Sonnet - AI 评估
- SQLite - 数据库

**前端**:
- React 18 + TypeScript
- Vite - 构建工具
- Ant Design - UI 组件库
- Axios - HTTP 客户端

## 快速开始

### 系统要求

- Python 3.10+
- Node.js 18+
- FFmpeg 4.0+
- 至少 8GB RAM
- 推荐使用 CUDA GPU（可选，用于加速）

### 安装步骤

#### 1. 克隆项目

```bash
cd ~/video-quality-system
```

#### 2. 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 ANTHROPIC_API_KEY
```

**重要**: 安装依赖可能需要 10-30 分钟，特别是 torch、whisper 等大型库。

#### 3. 前端安装

```bash
cd ../frontend

# 安装依赖
npm install
```

#### 4. 安装 FFmpeg

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows**:
下载 [FFmpeg](https://ffmpeg.org/download.html) 并添加到 PATH

### 启动应用

#### 方式 1: 使用启动脚本（推荐）

```bash
# 启动后端（在 backend 目录）
./start-backend.sh

# 启动前端（在 frontend 目录）
./start-frontend.sh
```

#### 方式 2: 手动启动

**后端**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端**:
```bash
cd frontend
npm run dev
```

### 访问应用

- 前端界面: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 使用指南

### 1. 上传视频

1. 访问 http://localhost:5173
2. 拖拽或点击上传视频文件
3. 支持格式: mp4, mov, avi
4. 推荐视频时长: 10-60 秒
5. 文件大小限制: 100MB

### 2. 自动分析

上传成功后，点击"开始分析"按钮，系统会自动：
1. 提取音频和关键帧
2. 进行语音识别（ASR）
3. 进行文字识别（OCR）
4. 检测场景切换
5. 分析产品位置和占比
6. 运行黄金3秒检测器
7. 运行 CTA 检测器
8. 分析剪辑节奏
9. 分析视觉重心
10. 计算规则评分
11. 调用 Claude AI 进行综合评估

**预计时长**: 30秒视频约需 1-2 分钟

### 3. 查看结果

分析完成后，结果页面会显示：

- **综合评分**: 0-100 分，等级 A+ 到 C
- **维度详情**:
  - 结构化分析: 黄金3秒评分、CTA 评分
  - 视觉动力学: 剪辑节奏、视觉重心
- **问题清单**: 按严重程度排序
- **AI 评估**:
  - 综合评价
  - 优势列表
  - 劣势列表
  - 改进建议

## API 文档

### 视频管理

#### 上传视频
```http
POST /api/videos/upload
Content-Type: multipart/form-data

file: <video_file>
```

响应:
```json
{
  "id": "vid_xxx",
  "filename": "test.mp4",
  "duration": 30.5,
  "resolution": "1920x1080",
  "fps": 30,
  "status": "uploaded"
}
```

#### 获取视频列表
```http
GET /api/videos/
```

#### 删除视频
```http
DELETE /api/videos/{video_id}
```

### 分析管理

#### 开始分析
```http
POST /api/analysis/start/{video_id}?use_ai=true
```

响应:
```json
{
  "task_id": "task_xxx",
  "video_id": "vid_xxx",
  "status": "processing"
}
```

#### 获取分析结果
```http
GET /api/analysis/result/{result_id}
```

#### 通过视频 ID 获取结果
```http
GET /api/analysis/result/by-video/{video_id}
```

响应示例:
```json
{
  "id": "result_xxx",
  "video_id": "vid_xxx",
  "overall_score": 78.5,
  "grade": "B+",
  "dimensions": {
    "structural": {
      "score": 85,
      "hook": {
        "score": 90,
        "detected": true,
        "hook_type": "question",
        "content": "你知道这个产品有多神奇吗?"
      },
      "cta": {
        "score": 80,
        "detected": true,
        "content": "点击购买"
      }
    },
    "visual": {
      "score": 72,
      "cut_frequency": {
        "score": 70,
        "avg_shot_length": 3.2,
        "total_cuts": 9
      },
      "saliency": {
        "score": 75,
        "avg_product_area": 0.35,
        "center_ratio": 0.78
      }
    }
  },
  "issues": [
    {
      "severity": "medium",
      "issue": "镜头5持续6.2秒无切换",
      "dimension": "visual"
    }
  ],
  "ai_evaluation": {
    "summary": "整体结构完整，开头吸引力强",
    "strengths": ["钩子设计巧妙", "产品展示清晰"],
    "weaknesses": ["中段节奏拖沓"],
    "recommendations": ["在12-18秒增加快节奏剪辑"]
  }
}
```

## 测试指南

### 端到端测试清单

#### 1. 上传功能测试
- [ ] 拖拽上传 mp4 文件
- [ ] 点击上传 mov 文件
- [ ] 上传进度显示正常
- [ ] 格式验证：尝试上传 .txt 文件（应该失败）
- [ ] 大小限制：尝试上传 >100MB 文件（应该提示错误）
- [ ] 上传成功后显示视频信息

#### 2. 分析功能测试

准备测试视频（放在 `test_videos/` 目录）:
- `good_hook.mp4` - 前3秒有明显钩子（疑问句或冲突感）
- `no_hook.mp4` - 前3秒平淡无奇
- `with_cta.mp4` - 结尾有明确行动指令
- `no_cta.mp4` - 结尾无行动指令
- `fast_cuts.mp4` - 快节奏剪辑（ASL < 2秒）
- `slow_cuts.mp4` - 慢节奏剪辑（ASL > 4秒）

测试步骤:
1. 上传 `good_hook.mp4`
2. 点击"开始分析"
3. 等待分析完成（1-2分钟）
4. 验证结果:
   - [ ] 黄金3秒检测应为高分（>70）
   - [ ] 检测到钩子类型
   - [ ] 显示具体内容

5. 重复测试其他视频，验证:
   - [ ] CTA 检测准确性
   - [ ] 剪辑节奏评分合理
   - [ ] 视觉重心分析准确

#### 3. AI 评估测试
- [ ] AI 评估返回有效的 JSON
- [ ] 优势列表相关且准确
- [ ] 劣势列表识别真实问题
- [ ] 改进建议具有可操作性
- [ ] 综合评价语句通顺

#### 4. 结果展示测试
- [ ] 总分显示正确（0-100）
- [ ] 等级显示正确（A+, A, B+, B, C）
- [ ] 进度圈渲染正常
- [ ] 维度详情展开完整
- [ ] 问题列表按严重程度排序
- [ ] AI 评估卡片显示完整

#### 5. 错误处理测试
- [ ] 上传无效文件格式
- [ ] 上传损坏的视频文件
- [ ] 无 Claude API Key 时的降级处理
- [ ] 网络中断时的错误提示
- [ ] 分析失败时的重试功能

### 性能测试

测试不同时长的视频处理时间:
- 10秒视频: 预期 < 30秒
- 30秒视频: 预期 < 2分钟
- 60秒视频: 预期 < 5分钟

## 故障排除

### 常见问题

#### 1. 依赖安装失败

**问题**: `pip install` 时出现编译错误

**解决**:
```bash
# macOS
brew install cmake pkg-config

# Ubuntu
sudo apt install build-essential cmake pkg-config
```

#### 2. Whisper 模型下载失败

**问题**: 首次运行时 Whisper 下载模型超时

**解决**:
```bash
# 手动下载模型
cd ~/.cache/whisper
wget https://openaipublic.azureedge.net/main/whisper/models/base.pt
```

#### 3. CUDA 不可用

**问题**: GPU 加速不工作

**解决**: 这是正常的，系统会自动降级到 CPU 模式。如需 GPU 加速，安装 CUDA 版本的 PyTorch:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 4. FFmpeg 找不到

**问题**: `FFmpeg not found`

**解决**:
```bash
# 验证安装
ffmpeg -version

# 如果未安装，参考"安装 FFmpeg"部分
```

#### 5. Claude API 调用失败

**问题**: `401 Unauthorized`

**解决**: 检查 `.env` 文件中的 `ANTHROPIC_API_KEY` 是否正确

#### 6. 分析速度慢

**问题**: 30秒视频分析需要 >5 分钟

**解决**:
- 检查是否有 GPU 可用
- 降低视频分辨率（系统会自动处理）
- 关闭 AI 评估（`use_ai=false`）
- 使用更小的 Whisper 模型（`WHISPER_MODEL=tiny`）

#### 7. PaddleOCR 安装问题

**问题**: PaddlePaddle 安装失败

**解决**:
```bash
# 使用 CPU 版本
pip install paddlepaddle==2.6.0 -i https://mirror.baidu.com/pypi/simple

# macOS M1/M2 芯片
pip install paddlepaddle-macos==2.6.0
```

## 性能优化

### 推荐配置

**开发环境**:
- CPU: 4核+
- RAM: 8GB+
- 存储: 20GB+

**生产环境**:
- CPU: 8核+
- RAM: 16GB+
- GPU: NVIDIA GPU with 4GB+ VRAM（可选）
- 存储: 100GB+ SSD

### 优化建议

1. **启用 GPU 加速**:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. **调整分析参数**（编辑 `backend/app/config.py`）:
```python
# 使用更小的 Whisper 模型
WHISPER_MODEL = "tiny"  # 从 "base" 改为 "tiny"

# 降低关键帧提取频率
EXTRACT_FPS = 0.5  # 从 1.0 降低到 0.5
```

3. **使用异步处理**（生产环境推荐）:
- 集成 Celery + Redis
- 分析任务后台执行
- WebSocket 实时推送进度

## 部署指南

### Docker 部署（推荐）

#### 1. 创建 Dockerfile

**后端 Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads temp logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

#### 2. Docker Compose

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/temp:/app/temp
      - ./backend/data:/app/data
    env_file:
      - ./backend/.env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

#### 3. 启动服务

```bash
docker-compose up -d
```

### 云部署

#### 准备工作

1. 选择云服务商（AWS, 阿里云, 腾讯云等）
2. 创建服务器实例（推荐配置：8核 16GB RAM）
3. 配置安全组（开放 80, 443, 8000 端口）

#### 部署步骤

1. **SSH 连接服务器**:
```bash
ssh user@your-server-ip
```

2. **安装依赖**:
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装 FFmpeg
sudo apt update && sudo apt install -y ffmpeg
```

3. **克隆代码**:
```bash
git clone <your-repo-url>
cd video-quality-system
```

4. **配置环境变量**:
```bash
cp backend/.env.example backend/.env
nano backend/.env  # 填入生产环境配置
```

5. **启动服务**:
```bash
docker-compose up -d
```

6. **配置 HTTPS**（使用 Let's Encrypt）:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 项目结构

```
video-quality-system/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置
│   │   ├── db.py              # 数据库
│   │   ├── api/               # API 路由
│   │   │   ├── videos.py
│   │   │   └── analysis.py
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # 核心功能
│   │   │   ├── extractors/    # 特征提取
│   │   │   ├── analyzers/     # 分析器
│   │   │   └── evaluators/    # 评分器
│   │   ├── integrations/      # 第三方集成
│   │   └── utils/             # 工具函数
│   ├── uploads/               # 上传文件
│   ├── temp/                  # 临时文件
│   ├── requirements.txt
│   └── .env
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   ├── services/          # API 服务
│   │   └── types/             # TypeScript 类型
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 评分规则

### 总分计算

```
总分 = 结构化分数 × 50% + 视觉分数 × 50%

结构化分数 = 黄金3秒 × 50% + CTA × 50%
视觉分数 = 剪辑节奏 × 50% + 视觉重心 × 50%
```

### 等级划分

- **A+**: 90-100 分 - 优秀
- **A**: 80-89 分 - 良好
- **B+**: 70-79 分 - 中等偏上
- **B**: 60-69 分 - 中等
- **C**: <60 分 - 需改进

### 各维度评分标准

#### 黄金3秒（0-100分）
- 文本评分（50%）:
  - 检测到冲突感词汇或疑问句: 50分
  - 未检测到: 20分
- 视觉评分（50%）:
  - 根据色彩饱和度变化计算: 0-50分

#### CTA 检测（0-100分）
- 检测到行动指令词汇: 100分
- 未检测到: 0分

#### 剪辑节奏（0-100分）
- 理想范围（1.5-3.0秒 ASL）: 100分
- 小于 1.5秒: 70-100分（按比例）
- 大于 3.0秒: 50-100分（按比例）
- 每个超长镜头（>5秒）扣 5分

#### 视觉重心（0-100分）
- 产品占比评分（40%）:
  - 理想范围（20%-50%）: 100分
  - 小于 20%: 按比例降分
  - 大于 50%: 轻微降分
- 中心度评分（40%）: 产品位置中心度 × 100
- 清晰度评分（20%）: 100 - (模糊帧比例 × 100)

## 开发指南

### 添加新的分析器

1. 在 `backend/app/core/analyzers/` 创建新文件
2. 实现分析器类:
```python
class NewAnalyzer:
    def analyze(self, video_path: str, **kwargs) -> Dict[str, any]:
        return {
            "score": 0-100,
            "detected": True/False,
            "details": {...},
            "issues": [...]
        }
```
3. 在 `analysis_service.py` 中集成
4. 更新前端结果展示页面

### 修改评分权重

编辑 `backend/app/core/evaluators/rule_evaluator.py`:
```python
self.weights = {
    "structural": 0.5,  # 调整权重
    "visual": 0.5
}
```

### 自定义 AI Prompt

编辑 `backend/app/core/evaluators/ai_evaluator.py` 中的 prompt 模板。

## 环境变量说明

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| ANTHROPIC_API_KEY | Claude API 密钥 | - | 是 |
| DATABASE_URL | 数据库连接字符串 | sqlite:///./video_quality.db | 否 |
| MAX_VIDEO_SIZE_MB | 最大视频大小（MB） | 100 | 否 |
| WHISPER_MODEL | Whisper 模型大小 | base | 否 |
| UPLOAD_DIR | 上传文件目录 | ./uploads | 否 |
| TEMP_DIR | 临时文件目录 | ./temp | 否 |
| EXTRACT_FPS | 关键帧提取帧率 | 1.0 | 否 |
| SUPPORTED_FORMATS | 支持的视频格式 | mp4,mov,avi | 否 |

## 常见问题 FAQ

### Q: 如何获取 Claude API Key？
A: 访问 https://console.anthropic.com/ 注册并创建 API Key。

### Q: 视频处理速度慢怎么办？
A:
- 使用更小的 Whisper 模型（tiny 或 base）
- 考虑使用 GPU 加速
- 降低关键帧提取频率（EXTRACT_FPS=0.5）
- 关闭 AI 评估（use_ai=false）

### Q: 安装依赖时出错？
A:
- 确保 Python 版本 >= 3.10
- 某些库需要系统依赖（如 FFmpeg）
- 对于 PaddlePaddle，参考官方文档选择合适的版本

### Q: 分析结果不准确？
A:
- 检查视频质量（分辨率、清晰度）
- 调整分析器参数（在各analyzer文件中）
- 收集更多测试样本，调整权重

### Q: 如何自定义评分规则？
A: 编辑 `backend/app/core/evaluators/rule_evaluator.py` 中的权重和阈值。

### Q: 支持哪些语言？
A: 目前支持中文和英文。Whisper 支持多语言，但分析器关键词以中文为主。

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持结构化和视觉分析
- 集成 Claude AI 评估
- Web 界面上传和结果展示

## 支持

如有问题，请提交 Issue 或联系开发团队。

---

**祝你使用愉快！**
