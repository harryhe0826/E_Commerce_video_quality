# 评分系统问题诊断与解决方案

## 问题现象

所有视频的评分都是固定的低分（如 22.5分），无论视频内容如何。

## 根本原因

**视频处理依赖库未安装**，导致特征提取器无法正常工作，返回空数据或默认值。

### 评分流程说明

```
视频上传
  ↓
特征提取 (Extractors)
  ├─ ASR (Whisper) → 语音文字
  ├─ OCR (PaddleOCR) → 屏幕文字
  ├─ 场景检测 (PySceneDetect) → 镜头切换
  └─ 视觉分析 (OpenCV + YOLO) → 产品检测
  ↓
分析器 (Analyzers)
  ├─ Hook检测 → 使用ASR/OCR文本
  ├─ CTA检测 → 使用ASR/OCR文本
  ├─ 剪辑节奏 → 使用场景数据
  └─ 视觉重心 → 使用视觉分析数据
  ↓
评分 (Evaluator)
  └─ 综合计算总分
```

### 当依赖库缺失时的默认返回值

| 提取器 | 缺失库 | 返回值 | 影响 |
|--------|--------|--------|------|
| AudioExtractor | Whisper | `{"text": "", "segments": []}` | Hook/CTA无法检测文本 |
| TextExtractor | PaddleOCR | `""` | Hook/CTA无法检测屏幕文字 |
| SceneExtractor | PySceneDetect | `[]` | 剪辑节奏默认50分 |
| VisualExtractor | OpenCV/YOLO | `{"avg_product_area": 0.0, ...}` | 视觉重心默认50分 |

### 默认评分计算

当所有提取器都返回空数据时：

1. **Hook检测** (黄金3秒):
   - 无文本 → text_score = 20
   - 无视觉变化 → visual_score = 0
   - **总分 = 20分**

2. **CTA检测** (行动指令):
   - 无文本 → 无法检测
   - **总分 = 0分**

3. **剪辑节奏**:
   - 场景为空 → **默认 50分**

4. **视觉重心**:
   - 产品区域为空 → **默认 50分**

**最终计算**:
```
结构化维度 = (Hook * 0.5 + CTA * 0.5) = (20 * 0.5 + 0 * 0.5) = 10分
视觉维度 = (剪辑 * 0.5 + 重心 * 0.5) = (50 * 0.5 + 50 * 0.5) = 50分

总分 = (结构化 * 0.5 + 视觉 * 0.5) = (10 * 0.5 + 50 * 0.5) = 30分
```

如果某些提取器返回略微不同的默认值，可能导致22.5分或其他固定分数。

## 解决方案

### 方案 1: 安装完整依赖（推荐用于生产环境）

安装所有视频处理库以获得完整功能：

```bash
cd /Users/harryhe/video-quality-system/backend

# 安装所有依赖（需要5-10分钟）
python3 -m pip install -r requirements.txt --user

# 或分步安装
python3 -m pip install numpy Pillow opencv-python --user
python3 -m pip install openai-whisper torch torchaudio --user
python3 -m pip install paddleocr paddlepaddle>=2.6.2 --user
python3 -m pip install "scenedetect[opencv]>=0.6.0" --user
python3 -m pip install ultralytics --user
```

安装完成后重启服务：
```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方案 2: 仅测试 AI 集成功能

如果只想测试 AI 集成（Aihubmix等），可以：

1. **使用模拟数据测试**

   创建测试脚本直接调用 AI 评估器：

```python
from app.integrations import EvaluatorFactory

# 创建评估器
evaluator = EvaluatorFactory.create_evaluator(
    platform="aihubmix",
    api_key="your_api_key",
    model="gpt-4o",
    base_url="https://aihubmix.com/v1"
)

# 模拟分析结果
mock_results = {
    "dimensions": {
        "structural": {
            "score": 85,
            "hook": {"score": 90, "detected": True, "hook_type": "question", "content": "你知道吗？"},
            "cta": {"score": 80, "detected": True, "cta_type": "direct"}
        },
        "visual": {
            "score": 88,
            "cut_frequency": {"score": 85, "avg_shot_length": 2.5, "total_cuts": 20},
            "saliency": {"score": 90, "avg_product_area": 0.35, "center_ratio": 0.8}
        }
    }
}

# 调用评估
result = evaluator.evaluate(
    key_frames=["/path/to/frame1.jpg", "/path/to/frame2.jpg", "/path/to/frame3.jpg"],
    asr_text="这是一个测试视频的语音文字",
    ocr_text="屏幕文字：立即购买！",
    analysis_results=mock_results
)

print(result)
```

2. **修改默认分数（临时方案，不推荐）**

   如果只想看到不同的分数，可以临时修改分析器的默认返回值：

   编辑 `/backend/app/core/analyzers/hook_detector.py` 第56行：
   ```python
   # 改为更高的默认分数
   text_score = 60  # 原来是 20
   ```

### 方案 3: 只安装必要的库

根据需要选择性安装：

```bash
# 只安装语音识别（ASR）
pip install openai-whisper torch torchaudio

# 只安装文字识别（OCR）
pip install paddleocr paddlepaddle>=2.6.2

# 只安装场景检测
pip install "scenedetect[opencv]>=0.6.0"

# 只安装视觉分析
pip install opencv-python ultralytics
```

## 验证修复

### 1. 检查依赖安装状态

运行后端服务时查看日志：

```bash
# 启动服务
python3 -m uvicorn app.main:app --reload

# 查看日志中的警告
# 应该看到类似信息：
# ✓ "Whisper model loaded successfully"
# ✓ "PaddleOCR initialized"
# ✓ "Scene detector ready"
```

如果看到警告信息：
```
⚠ "Whisper not installed. ASR功能不可用。"
⚠ "PaddleOCR not installed. OCR功能不可用。"
```
说明对应的库还未安装。

### 2. 测试视频分析

上传相同的视频，应该看到：
- **不同的分数**（不再是固定值）
- **详细的分析数据**（Hook检测、CTA检测等）
- **具体的问题和建议**

### 3. 查看分析详情

在 API 返回中应该包含：

```json
{
  "dimensions": {
    "structural": {
      "score": 75,  // 不再是固定的10分
      "hook": {
        "score": 80,
        "detected": true,
        "content": "实际检测到的文字"  // 不是空字符串
      },
      "cta": {
        "score": 70,
        "detected": true,
        "cta_type": "audio"
      }
    },
    "visual": {
      "score": 82,  // 不再是固定的50分
      "cut_frequency": {
        "score": 85,
        "total_cuts": 15,  // 实际的切换次数
        "avg_shot_length": 2.3
      }
    }
  }
}
```

## 快速诊断脚本

创建一个诊断脚本检查环境：

```python
#!/usr/bin/env python3
"""诊断视频处理依赖"""

print("🔍 检查视频处理依赖...\n")

libs = {
    "Whisper (ASR)": "whisper",
    "PaddleOCR": "paddleocr",
    "PySceneDetect": "scenedetect",
    "OpenCV": "cv2",
    "Ultralytics (YOLO)": "ultralytics",
    "NumPy": "numpy",
    "Pillow": "PIL"
}

for name, module in libs.items():
    try:
        __import__(module)
        print(f"✅ {name}: 已安装")
    except ImportError:
        print(f"❌ {name}: 未安装")

print("\n💡 提示：")
print("如需完整功能，请安装所有依赖：")
print("  pip install -r requirements.txt")
```

## 推荐方案

**对于你的情况**，建议：

1. **如果需要完整的视频分析功能**：
   - 执行方案1，安装所有依赖
   - 预计安装时间：5-10分钟（取决于网络速度）
   - 磁盘空间需求：约2-3GB

2. **如果只测试 AI 集成（Aihubmix）**：
   - 当前环境已足够
   - 使用方案2的模拟数据测试
   - AI 评估功能完全可用

3. **如果需要真实视频分析但资源有限**：
   - 至少安装 Whisper + PaddleOCR（用于文本分析）
   - 这样可以让 Hook 和 CTA 检测正常工作
   - 评分会更加准确

## 参考资源

- [完整依赖列表](requirements.txt)
- [AI 集成指南](AI_INTEGRATION_GUIDE.md)
- [测试脚本](test_ai_integration.py)
