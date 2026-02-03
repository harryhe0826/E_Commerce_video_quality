# 前端 AI 平台集成更新

## 更新内容

前端已更新以支持多个 AI 平台配置，包括 Claude、Aihubmix 和 OpenAI。

## 主要变更

### 1. 设置界面更新 ([SettingsModal.tsx](src/components/SettingsModal.tsx))

新增功能：
- ✅ **平台选择器** - 支持选择 Claude、Aihubmix、OpenAI
- ✅ **API Key 配置** - 针对不同平台的 API Key 输入
- ✅ **模型选择** - 每个平台支持多个模型选择
- ✅ **Base URL 配置** - 第三方平台（如 Aihubmix）支持自定义 Base URL
- ✅ **向后兼容** - 自动迁移旧版本的 Claude API Key

### 2. API 服务更新 ([analysisService.ts](src/services/analysisService.ts))

新增功能：
- ✅ 自动从 localStorage 读取多平台配置
- ✅ 发送正确的 HTTP headers（x-ai-platform, x-ai-api-key, x-ai-model, x-ai-base-url）
- ✅ 向后兼容旧版本配置

## 支持的平台

### 1. Claude (Anthropic)
- **模型**: claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-sonnet-20240229
- **说明**: 官方 Claude API，高质量输出
- **获取 API Key**: https://console.anthropic.com/

### 2. Aihubmix（推荐）
- **模型**: gpt-4o, claude-3-5-sonnet-20241022, gemini-pro, deepseek-chat, qwen-max, gpt-3.5-turbo
- **Base URL**: https://aihubmix.com/v1
- **说明**: 第三方聚合平台，支持多种模型，价格灵活
- **获取 API Key**: https://aihubmix.com

### 3. OpenAI
- **模型**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Base URL**: https://api.openai.com/v1
- **说明**: 官方 OpenAI API，响应速度快
- **获取 API Key**: https://platform.openai.com

## 使用方法

### 步骤 1: 配置 AI 平台

1. 启动前端应用
2. 点击右上角的设置按钮 ⚙️
3. 选择要使用的 AI 平台
4. 输入对应的 API Key
5. （可选）选择模型
6. （可选）配置 Base URL（仅 Aihubmix）
7. 点击保存

### 步骤 2: 开始分析

1. 上传视频
2. 勾选"使用 AI 评估"
3. 点击"开始分析"
4. 系统会自动使用你配置的平台和模型

## 配置存储

所有配置保存在浏览器的 localStorage 中：
- **新格式**: `ai_settings` (JSON)
  ```json
  {
    "platform": "aihubmix",
    "apiKey": "your_api_key",
    "model": "gpt-4o",
    "baseUrl": "https://aihubmix.com/v1"
  }
  ```
- **旧格式**: `claude_api_key` (字符串) - 仍然支持，会自动迁移

## 数据流

```
用户配置 (localStorage)
    ↓
analysisService.getAISettings()
    ↓
HTTP Headers:
  - x-ai-platform: "aihubmix"
  - x-ai-api-key: "your_key"
  - x-ai-model: "gpt-4o"
  - x-ai-base-url: "https://aihubmix.com/v1"
    ↓
后端 API (/api/analysis/start/{video_id})
    ↓
EvaluatorFactory.create_evaluator()
    ↓
AI 平台评估
```

## 兼容性说明

### 向后兼容
- ✅ 旧版本只配置了 Claude API Key 的用户，配置会自动迁移
- ✅ 旧的 `X-Claude-API-Key` header 仍然支持
- ✅ 新旧配置格式同时支持

### 浏览器兼容性
- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- 需要支持 localStorage 和 ES6

## 开发说明

### 启动开发服务器

```bash
cd frontend
npm install
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 测试配置

在浏览器控制台中查看保存的配置：

```javascript
// 查看当前配置
JSON.parse(localStorage.getItem('ai_settings'))

// 手动设置配置（测试用）
localStorage.setItem('ai_settings', JSON.stringify({
  platform: 'aihubmix',
  apiKey: 'your_test_key',
  model: 'gpt-4o',
  baseUrl: 'https://aihubmix.com/v1'
}))
```

## 示例截图说明

### 设置界面功能

1. **平台选择下拉框**
   - 显示 3 个平台选项
   - 切换平台时自动更新模型列表

2. **API Key 输入**
   - 密码输入框，保护隐私
   - 显示已保存的 Key（脱敏）
   - 提供获取链接

3. **模型选择**
   - 根据平台动态显示可用模型
   - 显示默认推荐模型

4. **Base URL 配置**
   - 仅在需要时显示（如 Aihubmix）
   - 显示默认值

5. **平台说明**
   - 每个平台的特点介绍
   - 适用场景说明

## 故障排查

### 问题 1: 配置保存后不生效
**解决方案**:
1. 清除浏览器缓存
2. 检查浏览器控制台是否有错误
3. 验证 localStorage 中的配置格式

### 问题 2: API 调用失败
**解决方案**:
1. 检查 Network 面板中的请求 headers
2. 确认 API Key 是否正确
3. 确认后端服务是否运行
4. 查看后端日志

### 问题 3: 旧配置迁移失败
**解决方案**:
1. 手动清除旧配置: `localStorage.removeItem('claude_api_key')`
2. 重新在设置界面配置

## 后续优化建议

1. **配置导入导出** - 支持配置的导入导出功能
2. **多配置管理** - 支持保存多个平台配置，快速切换
3. **配置验证** - 添加 API Key 验证功能
4. **使用统计** - 显示不同平台的使用情况和成本
5. **错误提示** - 更详细的错误信息和解决建议

## 相关文档

- [后端 AI 集成指南](../backend/AI_INTEGRATION_GUIDE.md)
- [API 文档](http://localhost:8000/docs)
- [Aihubmix 官方文档](https://doc.aihubmix.com)

## 更新日志

- **2024-02-03**: 初始版本，支持 Claude、Aihubmix、OpenAI 三个平台
