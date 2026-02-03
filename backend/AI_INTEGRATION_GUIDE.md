# 第三方大模型平台 API 集成文档

本文档介绍如何在视频质量分析系统中使用第三方大模型聚合平台的 API 接口。

## 支持的平台

系统现已支持以下 AI 平台：

1. **Claude (Anthropic)** - 官方 Claude API
2. **Aihubmix** - 第三方大模型聚合平台（支持 Claude、GPT-4、Gemini、Qwen、Deepseek 等）
3. **OpenAI** - 官方 OpenAI API
4. **其他 OpenAI 兼容平台** - 如 new-api、one-api 等

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增的依赖：
- `openai>=1.0.0` - 支持 OpenAI 兼容的第三方平台

### 2. 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
```

根据你要使用的平台配置相应的环境变量：

#### 使用 Aihubmix（推荐）

```env
# 设置默认平台为 aihubmix
AI_PLATFORM=aihubmix

# Aihubmix 配置
AIHUBMIX_API_KEY=your_aihubmix_api_key_here
AIHUBMIX_BASE_URL=https://aihubmix.com/v1
AIHUBMIX_MODEL=gpt-4o
```

支持的模型包括：
- `gpt-4o` - GPT-4 Optimized
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `gemini-pro` - Google Gemini Pro
- `deepseek-chat` - Deepseek Chat
- `qwen-max` - 阿里千问 Max
- 更多模型请查看 [Aihubmix 文档](https://doc.aihubmix.com)

#### 使用 Claude

```env
AI_PLATFORM=claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### 使用 OpenAI

```env
AI_PLATFORM=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

### 3. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 使用方法

### 方法 1: 使用默认配置

如果在 `.env` 文件中配置了默认平台，可以直接调用：

```bash
curl -X POST "http://localhost:8000/api/analysis/start/{video_id}?use_ai=true"
```

### 方法 2: 通过 HTTP Headers 动态指定平台

可以在请求时通过 HTTP headers 动态指定 AI 平台和参数：

#### 使用 Aihubmix

```bash
curl -X POST "http://localhost:8000/api/analysis/start/{video_id}?use_ai=true" \
  -H "x-ai-platform: aihubmix" \
  -H "x-ai-api-key: your_aihubmix_api_key" \
  -H "x-ai-model: gpt-4o" \
  -H "x-ai-base-url: https://aihubmix.com/v1"
```

#### 使用 Claude（新方式）

```bash
curl -X POST "http://localhost:8000/api/analysis/start/{video_id}?use_ai=true" \
  -H "x-ai-platform: claude" \
  -H "x-ai-api-key: your_anthropic_api_key" \
  -H "x-ai-model: claude-3-5-sonnet-20241022"
```

#### 使用 Claude（旧方式，向后兼容）

```bash
curl -X POST "http://localhost:8000/api/analysis/start/{video_id}?use_ai=true" \
  -H "x-claude-api-key: your_anthropic_api_key"
```

### 支持的 HTTP Headers

| Header | 说明 | 示例 |
|--------|------|------|
| `x-ai-platform` | AI 平台名称 | `claude`, `aihubmix`, `openai` |
| `x-ai-api-key` | API 密钥 | `your_api_key_here` |
| `x-ai-model` | 模型名称 | `gpt-4o`, `claude-3-5-sonnet-20241022` |
| `x-ai-base-url` | API 基础 URL | `https://aihubmix.com/v1` |
| `x-claude-api-key` | Claude API Key（向后兼容） | `your_anthropic_api_key` |

## 前端集成示例

### JavaScript / TypeScript

```typescript
// 使用 Aihubmix
const response = await fetch(`/api/analysis/start/${videoId}?use_ai=true`, {
  method: 'POST',
  headers: {
    'x-ai-platform': 'aihubmix',
    'x-ai-api-key': 'your_aihubmix_api_key',
    'x-ai-model': 'gpt-4o',
    'x-ai-base-url': 'https://aihubmix.com/v1'
  }
});

// 或使用默认配置
const response = await fetch(`/api/analysis/start/${videoId}?use_ai=true`, {
  method: 'POST'
});
```

### Python

```python
import requests

# 使用 Aihubmix
response = requests.post(
    f"http://localhost:8000/api/analysis/start/{video_id}",
    params={"use_ai": True},
    headers={
        "x-ai-platform": "aihubmix",
        "x-ai-api-key": "your_aihubmix_api_key",
        "x-ai-model": "gpt-4o",
        "x-ai-base-url": "https://aihubmix.com/v1"
    }
)
```

## 架构说明

### 代码组织

```
backend/app/
├── integrations/                    # 第三方平台集成
│   ├── __init__.py                 # 工厂类和导出
│   ├── base_evaluator.py           # 抽象基类
│   ├── claude_evaluator.py         # Claude 评估器
│   ├── aihubmix_evaluator.py       # Aihubmix 评估器
│   └── ...                         # 其他平台评估器
├── services/
│   └── analysis_service.py         # 分析服务（调用评估器）
└── api/
    └── analysis.py                 # API 路由
```

### 工厂模式

系统使用工厂模式创建评估器实例：

```python
from app.integrations import EvaluatorFactory

# 创建评估器
evaluator = EvaluatorFactory.create_evaluator(
    platform="aihubmix",
    api_key="your_api_key",
    model="gpt-4o",
    base_url="https://aihubmix.com/v1"
)

# 使用评估器
result = evaluator.evaluate(key_frames, asr_text, ocr_text, analysis_results)
```

### 添加新平台

如果需要支持新的 AI 平台，只需：

1. 继承 `BaseAIEvaluator` 类
2. 实现 `_initialize_client()` 和 `evaluate()` 方法
3. 在 `EvaluatorFactory.SUPPORTED_PLATFORMS` 中注册

示例：

```python
from app.integrations.base_evaluator import BaseAIEvaluator

class CustomEvaluator(BaseAIEvaluator):
    def _initialize_client(self):
        # 初始化客户端
        pass

    def evaluate(self, key_frames, asr_text, ocr_text, analysis_results):
        # 实现评估逻辑
        pass
```

## 注意事项

1. **API Key 安全**: 不要在代码中硬编码 API Key，使用环境变量或 HTTP headers
2. **成本控制**: 不同平台和模型的价格不同，请根据需求选择
3. **速率限制**: 注意各平台的 API 调用频率限制
4. **向后兼容**: 旧的 `x-claude-api-key` header 仍然支持，会自动使用 Claude 平台

## 获取 API Key

### Aihubmix
1. 访问 [https://aihubmix.com](https://aihubmix.com)
2. 注册账号
3. 在控制台生成 API Key
4. 查看[官方文档](https://doc.aihubmix.com)

### Claude (Anthropic)
1. 访问 [https://console.anthropic.com](https://console.anthropic.com)
2. 创建账号
3. 生成 API Key

### OpenAI
1. 访问 [https://platform.openai.com](https://platform.openai.com)
2. 创建账号
3. 生成 API Key

## 常见问题

### Q: 如何切换不同的 AI 平台？

**A**: 有三种方式：
1. 修改 `.env` 文件中的 `AI_PLATFORM` 变量（全局默认）
2. 在 API 请求时通过 `x-ai-platform` header 指定（单次请求）
3. 前端提供设置界面让用户选择

### Q: Aihubmix 支持哪些模型？

**A**: Aihubmix 支持多种模型，包括：
- OpenAI: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- Anthropic: claude-3-5-sonnet, claude-3-opus
- Google: gemini-pro, gemini-ultra
- 国产: deepseek-chat, qwen-max, glm-4
- 具体请查看[官方模型列表](https://doc.aihubmix.com/en/)

### Q: 如何处理 API 调用失败？

**A**: 系统已内置错误处理，会返回包含错误信息的响应。建议：
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看日志文件了解详细错误信息

### Q: 性能和成本对比？

**A**:
- **Claude**: 高质量输出，价格适中，适合对质量要求高的场景
- **Aihubmix**: 提供多种模型选择，价格灵活，适合需要切换不同模型的场景
- **OpenAI**: GPT-4o 性价比高，响应速度快

## 参考资源

- [Aihubmix 官方文档](https://doc.aihubmix.com)
- [Claude API 文档](https://docs.anthropic.com)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [项目 README](../README.md)

## 更新日志

- **2024-02**: 新增对第三方大模型聚合平台的支持（Aihubmix 等）
- 实现评估器工厂模式
- 支持通过 HTTP headers 动态指定平台
- 向后兼容旧版 API
