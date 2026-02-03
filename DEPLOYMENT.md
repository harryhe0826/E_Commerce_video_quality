# 部署指南 (Deployment Guide)

## 🚀 前端部署到 Vercel

### 方法 1: 通过 Vercel Dashboard（推荐）

1. 访问 [Vercel](https://vercel.com)
2. 点击 "New Project"
3. 导入你的 GitHub 仓库：`https://github.com/harryhe0826/E_Commerce_video_quality`
4. 配置项目：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. 添加环境变量：
   - `VITE_API_URL`: 你的后端 API 地址（见下文）
6. 点击 "Deploy"

### 方法 2: 通过 Vercel CLI

```bash
cd frontend
npm install -g vercel
vercel
```

---

## 🖥️ 后端部署选项

### 推荐平台 1: Railway (最简单)

**特点**：
- ✅ 支持 Docker
- ✅ 自动 HTTPS
- ✅ 持久化存储
- ✅ 免费额度

**部署步骤**：

1. 在项目根目录创建 `Dockerfile`（见下文）
2. 访问 [Railway.app](https://railway.app)
3. 连接 GitHub 仓库
4. 选择 "Deploy from GitHub"
5. 添加环境变量（`.env`）
6. 部署完成后获取 API URL

### 推荐平台 2: Render

**特点**：
- ✅ 免费层级
- ✅ 自动部署
- ✅ 持久化磁盘

**部署步骤**：

1. 访问 [Render.com](https://render.com)
2. 创建 "New Web Service"
3. 连接 GitHub 仓库
4. 配置：
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 添加磁盘存储用于文件上传
6. 部署

### 推荐平台 3: Fly.io

适合需要更多控制的场景，支持 Docker。

---

## 🐳 Docker 配置（用于 Railway/Fly.io）

在项目根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制后端文件
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# 创建必要的目录
RUN mkdir -p uploads temp logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔗 连接前后端

部署后端后，你会获得一个 API URL（例如：`https://your-backend.railway.app`）

### 更新前端 API 地址：

1. 在 Vercel 项目设置中添加环境变量：
   ```
   VITE_API_URL=https://your-backend.railway.app
   ```

2. 或者直接修改 `frontend/src/services/analysisService.ts`：
   ```typescript
   const API_BASE_URL = 'https://your-backend.railway.app/api'
   ```

---

## 🗄️ 数据库选择

对于生产环境，建议将 SQLite 替换为云数据库：

### 选项 1: PostgreSQL（推荐）
- Railway 自带 PostgreSQL
- 或使用 [Supabase](https://supabase.com)（免费）

### 选项 2: MySQL
- [PlanetScale](https://planetscale.com)（免费层级）

---

## 📝 环境变量配置

### 后端环境变量 (`.env`)：

```bash
# AI API Keys
AIHUBMIX_API_KEY=your_aihubmix_key
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
AIHUBMIX_MODEL=moonshot-kimi-k2.5

# 或者使用 Claude
ANTHROPIC_API_KEY=your_claude_key

# 或者使用 OpenAI
OPENAI_API_KEY=your_openai_key

# 其他配置
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
MAX_VIDEO_SIZE_MB=100
```

---

## ✅ 部署检查清单

- [ ] 前端成功部署到 Vercel
- [ ] 后端成功部署到 Railway/Render
- [ ] 环境变量已配置
- [ ] 前端 API URL 已更新
- [ ] CORS 配置正确
- [ ] 数据库连接正常
- [ ] 文件上传功能正常
- [ ] AI 评估功能正常

---

## 🔧 故障排除

### 问题：前端无法连接后端
**解决**：检查 CORS 设置，确保后端允许前端域名

### 问题：视频上传失败
**解决**：检查后端存储空间和上传大小限制

### 问题：AI 评估超时
**解决**：增加后端服务器的超时限制

---

## 💰 成本估算

### 免费方案：
- **前端 (Vercel)**: 免费
- **后端 (Railway)**: $5/月（免费试用）
- **数据库**: 免费（SQLite 或免费 PostgreSQL）
- **总计**: ~$5/月

### 生产方案：
- **前端 (Vercel Pro)**: $20/月
- **后端 (Railway Pro)**: $20/月
- **数据库 (Supabase Pro)**: $25/月
- **总计**: ~$65/月
