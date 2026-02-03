# 前端部署指南 - Vercel

## 使用 Vercel CLI 部署

1. 安装 Vercel CLI（如果还没安装）：
```bash
npm install -g vercel
```

2. 在项目根目录登录 Vercel：
```bash
vercel login
```

3. 部署项目：
```bash
vercel
```

4. 按照提示操作：
   - Set up and deploy? **Yes**
   - Which scope? 选择你的账户
   - Link to existing project? **No**
   - What's your project's name? **video-quality-system**（或其他名称）
   - In which directory is your code located? **.**（当前目录）
   - Want to override the settings? **Yes**
     - Build Command: `cd frontend && npm install && npm run build`
     - Output Directory: `frontend/dist`
     - Development Command: `cd frontend && npm run dev`

5. 部署成功后，配置环境变量：
```bash
vercel env add VITE_API_URL production
```
   然后输入你的 Railway 后端 URL（例如：`https://your-service.railway.app`）

6. 重新部署以应用环境变量：
```bash
vercel --prod
```

## 使用 Vercel 网页界面部署

1. 访问 https://vercel.com
2. 点击 "New Project"
3. 导入你的 GitHub 仓库：`harryhe0826/E_Commerce_video_quality`
4. 配置项目：
   - Framework Preset: **Vite**
   - Root Directory: **/**（保持为根目录）
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
   - Install Command: `cd frontend && npm install`

5. 添加环境变量：
   - 点击 "Environment Variables"
   - Name: `VITE_API_URL`
   - Value: 你的 Railway 后端 URL（例如：`https://your-service.railway.app`）
   - 选择所有环境：Production, Preview, Development

6. 点击 "Deploy"

## 部署后验证

1. 访问 Vercel 提供的 URL
2. 尝试上传视频并查看分析结果
3. 检查浏览器控制台是否有错误

## 故障排除

如果遇到 API 连接问题：
1. 检查 Railway 后端是否正常运行
2. 确认 VITE_API_URL 环境变量设置正确（不要在 URL 末尾加 /）
3. 检查 Railway 后端的 CORS 设置
4. 在 Vercel 部署日志中查看构建错误
