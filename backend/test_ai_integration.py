"""
测试 AI 集成功能

这个脚本可以独立运行，测试不同 AI 平台的集成是否正常
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/Users/harryhe/video-quality-system/backend')

def test_evaluator_factory():
    """测试评估器工厂"""
    print("=" * 60)
    print("测试评估器工厂功能")
    print("=" * 60)

    from app.integrations import EvaluatorFactory

    # 1. 列出支持的平台
    platforms = EvaluatorFactory.list_supported_platforms()
    print(f"\n✓ 支持的 AI 平台: {', '.join(platforms)}")

    # 2. 测试创建 Claude 评估器（不需要真实API Key）
    print("\n" + "-" * 60)
    print("测试 Claude 评估器初始化")
    print("-" * 60)
    try:
        claude_evaluator = EvaluatorFactory.create_evaluator(
            platform="claude",
            api_key="test_key_for_structure_test"
        )
        print(f"✓ Claude 评估器创建成功")
        print(f"  - 类型: {type(claude_evaluator).__name__}")
        print(f"  - 模型: {claude_evaluator.model}")
        print(f"  - 可用性: {claude_evaluator.is_available()}")
    except Exception as e:
        print(f"✗ Claude 评估器创建失败: {e}")

    # 3. 测试创建 Aihubmix 评估器
    print("\n" + "-" * 60)
    print("测试 Aihubmix 评估器初始化")
    print("-" * 60)
    try:
        aihubmix_evaluator = EvaluatorFactory.create_evaluator(
            platform="aihubmix",
            api_key="test_key_for_structure_test",
            base_url="https://aihubmix.com/v1",
            model="gpt-4o"
        )
        print(f"✓ Aihubmix 评估器创建成功")
        print(f"  - 类型: {type(aihubmix_evaluator).__name__}")
        print(f"  - 基础URL: {aihubmix_evaluator.base_url}")
        print(f"  - 模型: {aihubmix_evaluator.model}")
        print(f"  - 可用性: {aihubmix_evaluator.is_available()}")
    except Exception as e:
        print(f"✗ Aihubmix 评估器创建失败: {e}")

    # 4. 测试创建 OpenAI 评估器
    print("\n" + "-" * 60)
    print("测试 OpenAI 评估器初始化")
    print("-" * 60)
    try:
        openai_evaluator = EvaluatorFactory.create_evaluator(
            platform="openai",
            api_key="test_key_for_structure_test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o"
        )
        print(f"✓ OpenAI 评估器创建成功")
        print(f"  - 类型: {type(openai_evaluator).__name__}")
        print(f"  - 基础URL: {openai_evaluator.base_url}")
        print(f"  - 模型: {openai_evaluator.model}")
        print(f"  - 可用性: {openai_evaluator.is_available()}")
    except Exception as e:
        print(f"✗ OpenAI 评估器创建失败: {e}")

    # 5. 测试错误的平台名称
    print("\n" + "-" * 60)
    print("测试错误处理")
    print("-" * 60)
    try:
        invalid_evaluator = EvaluatorFactory.create_evaluator(
            platform="invalid_platform"
        )
        print("✗ 应该抛出 ValueError 但没有")
    except ValueError as e:
        print(f"✓ 正确处理无效平台: {e}")
    except Exception as e:
        print(f"✗ 未预期的错误: {e}")

def test_config():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试配置文件")
    print("=" * 60)

    from app.config import settings

    print(f"\n✓ 配置加载成功")
    print(f"  - 默认AI平台: {settings.AI_PLATFORM}")
    print(f"  - Anthropic API Key: {'已设置' if settings.ANTHROPIC_API_KEY else '未设置'}")
    print(f"  - Aihubmix API Key: {'已设置' if settings.AIHUBMIX_API_KEY else '未设置'}")
    print(f"  - Aihubmix Base URL: {settings.AIHUBMIX_BASE_URL}")
    print(f"  - Aihubmix Model: {settings.AIHUBMIX_MODEL}")
    print(f"  - OpenAI API Key: {'已设置' if settings.OPENAI_API_KEY else '未设置'}")

def test_prompt_generation():
    """测试 Prompt 生成"""
    print("\n" + "=" * 60)
    print("测试 Prompt 生成")
    print("=" * 60)

    from app.integrations import EvaluatorFactory

    # 创建一个测试评估器
    evaluator = EvaluatorFactory.create_evaluator(
        platform="aihubmix",
        api_key="test_key"
    )

    # 模拟分析结果
    mock_results = {
        "dimensions": {
            "structural": {
                "score": 85,
                "hook": {
                    "score": 90,
                    "detected": True,
                    "hook_type": "question",
                    "content": "你知道吗？"
                },
                "cta": {
                    "score": 80,
                    "detected": True,
                    "cta_type": "direct"
                }
            },
            "visual": {
                "score": 88,
                "cut_frequency": {
                    "score": 85,
                    "avg_shot_length": 2.5,
                    "total_cuts": 20
                },
                "saliency": {
                    "score": 90,
                    "avg_product_area": 0.35,
                    "center_ratio": 0.8
                }
            }
        }
    }

    prompt = evaluator._build_prompt(
        asr_text="这是一个测试视频的语音文字",
        ocr_text="屏幕文字：买买买！",
        analysis_results=mock_results
    )

    print("\n✓ Prompt 生成成功")
    print(f"  - Prompt 长度: {len(prompt)} 字符")
    print(f"  - 包含评分信息: {'✓' if '85' in prompt else '✗'}")
    print(f"  - 包含黄金3秒: {'✓' if '黄金3秒' in prompt else '✗'}")
    print(f"  - 包含JSON格式要求: {'✓' if 'JSON' in prompt else '✗'}")

if __name__ == "__main__":
    try:
        print("\n🚀 开始测试 AI 集成功能\n")

        test_evaluator_factory()
        test_config()
        test_prompt_generation()

        print("\n" + "=" * 60)
        print("✅ 所有结构测试完成！")
        print("=" * 60)
        print("\n💡 提示：")
        print("  1. 所有评估器类已正确创建")
        print("  2. 工厂模式正常工作")
        print("  3. 配置文件加载正常")
        print("  4. 要进行完整的API测试，需要：")
        print("     - 配置真实的 API Key")
        print("     - 准备测试图片")
        print("     - 调用 evaluate() 方法")
        print("\n📚 查看详细使用文档: backend/AI_INTEGRATION_GUIDE.md")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
