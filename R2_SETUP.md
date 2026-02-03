# Cloudflare R2 对象存储集成指南

本指南将帮助你配置 Cloudflare R2 对象存储，用于持久化存储视频文件。

## 为什么需要 R2？

在 Railway 等云平台上，文件系统是临时的（ephemeral），每次部署或重启后上传的文件都会丢失。使用 Cloudflare R2 对象存储可以：

- ✅ 持久化存储视频文件
- ✅ 不限流量的免费出口
- ✅ S3 兼容 API，易于集成
- ✅ 每月 10GB 免费存储空间

## 步骤 1: 创建 Cloudflare R2 Bucket

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 在左侧导航栏选择 **R2**
3. 点击 **Create bucket** 按钮
4. 输入 bucket 名称，例如：`video-quality-uploads`
5. 选择区域（建议选择离你用户最近的区域）
6. 点击 **Create bucket**

## 步骤 2: 获取 R2 API 凭证

1. 在 R2 页面，点击右上角的 **Manage R2 API Tokens**
2. 点击 **Create API token** 按钮
3. 配置 API token：
   - **Token name**: 例如 `video-quality-api`
   - **Permissions**: 选择 **Object Read & Write** (读写权限)
   - **TTL**: 选择 **Forever** (永久有效) 或设置过期时间
   - **Apply to specific buckets only**: 选择刚创建的 bucket
4. 点击 **Create API Token**
5. **重要**: 保存以下信息（只会显示一次）：
   - `Access Key ID`
   - `Secret Access Key`
   - `Endpoint URL` (格式: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`)

## 步骤 3: 获取 Account ID

1. 在 Cloudflare Dashboard 中，点击右上角的账户名
2. 在侧边栏中找到 **Account ID**
3. 复制保存这个 ID

## 步骤 4: 配置本地环境（可选 - 用于本地测试）

如果你想在本地测试 R2 集成，创建 `backend/.env` 文件：

```bash
# 启用 R2 存储
USE_R2_STORAGE=True

# R2 配置
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_id_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here
R2_BUCKET_NAME=video-quality-uploads

# R2 公共访问域名（可选）
# 如果配置了 custom domain，填写这里
R2_PUBLIC_URL=
```

然后安装依赖并运行：

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## 步骤 5: 在 Railway 配置 R2 环境变量

1. 打开你的 [Railway Dashboard](https://railway.app/)
2. 选择你的项目
3. 点击 **Variables** 标签
4. 添加以下环境变量：

```
USE_R2_STORAGE=True
R2_ACCOUNT_ID=<你的 Account ID>
R2_ACCESS_KEY_ID=<你的 Access Key ID>
R2_SECRET_ACCESS_KEY=<你的 Secret Access Key>
R2_BUCKET_NAME=video-quality-uploads
```

5. 点击 **Add** 或 **Deploy** 保存更改
6. Railway 会自动重新部署应用

## 步骤 6: 验证配置

部署完成后，测试上传功能：

1. 访问你的前端应用
2. 尝试上传一个测试视频
3. 检查 Railway 日志，应该看到类似的日志：
   ```
   R2 Storage Service initialized with bucket: video-quality-uploads
   File uploaded to R2: videos/vid_xxxxxxxxxxxx.mp4
   ```

4. 在 Cloudflare R2 Dashboard 中，进入你的 bucket，应该能看到上传的视频文件

## 可选：配置 R2 Public URL (Custom Domain)

如果你想通过自定义域名访问 R2 文件：

1. 在 R2 bucket 设置中，点击 **Settings**
2. 找到 **Custom Domains** 部分
3. 点击 **Connect Domain**
4. 按照提示添加 DNS 记录
5. 配置完成后，在 Railway 中添加环境变量：
   ```
   R2_PUBLIC_URL=https://your-custom-domain.com
   ```

## 常见问题

### Q: R2 收费吗？

A: Cloudflare R2 提供免费额度：
- 10 GB/月 存储空间
- 1,000,000 次/月 Class A 操作（写入、列表）
- 10,000,000 次/月 Class B 操作（读取）
- **零出口流量费用**（这是 R2 相比 S3 的最大优势）

超出免费额度后的定价：
- 存储: $0.015/GB/月
- Class A 操作: $4.50/百万次
- Class B 操作: $0.36/百万次

### Q: 如何禁用 R2，恢复本地存储？

A: 在 Railway 环境变量中设置：
```
USE_R2_STORAGE=False
```

或者直接删除这个环境变量。

### Q: 可以使用其他对象存储服务吗？

A: 可以！由于使用了 S3 兼容 API（boto3），你可以轻松切换到：
- AWS S3
- 阿里云 OSS
- 腾讯云 COS
- MinIO (自建)
- Railway Blob Storage (即将支持)

只需修改 `storage_service.py` 中的 `endpoint_url` 和凭证配置即可。

## 架构说明

集成 R2 后的工作流程：

1. **视频上传**:
   - 前端上传文件到后端
   - 后端将文件上传到 R2
   - 数据库存储 R2 文件的 URL

2. **视频分析**:
   - 从 R2 下载视频到临时文件
   - 执行分析（ASR、OCR、场景检测等）
   - 分析完成后删除临时文件

3. **视频播放** (未来功能):
   - 前端通过 R2 URL 直接访问视频
   - 或者通过后端生成签名 URL（私有访问）

## 技术细节

- **boto3**: AWS SDK for Python，用于 S3 兼容 API
- **S3 兼容性**: R2 完全兼容 S3 API
- **临时文件管理**: 视频分析时会下载到 `temp/` 目录，分析完成后自动清理
- **错误处理**: 如果 R2 不可用，会返回友好的错误信息

## 下一步

配置完成后，你可以：

1. 测试完整的视频上传和分析流程
2. 查看 Railway 日志确认 R2 集成正常工作
3. 在 Cloudflare Dashboard 中监控 R2 使用情况
4. （可选）配置 CDN 加速视频访问

## 需要帮助？

如果遇到问题，请检查：

1. Railway 日志中是否有 R2 相关错误
2. Cloudflare R2 API Token 权限是否正确
3. Bucket 名称是否匹配
4. 环境变量是否正确设置

---

📝 **提示**: 建议先在本地测试 R2 配置，确认无误后再部署到 Railway。
