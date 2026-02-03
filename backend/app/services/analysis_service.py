"""
分析服务 - 编排完整的视频分析流程
"""
import os
import json
import uuid
import numpy as np
from typing import Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.db import Video, AnalysisResult
from app.config import settings
from app.utils.video_utils import extract_audio, extract_key_frames, get_video_info

# 特征提取器
from app.core.extractors.audio_extractor import get_audio_extractor
from app.core.extractors.text_extractor import get_text_extractor
from app.core.extractors.scene_extractor import get_scene_extractor
from app.core.extractors.visual_extractor import get_visual_extractor

# 分析器
from app.core.analyzers.hook_detector import HookDetector
from app.core.analyzers.cta_detector import CTADetector
from app.core.analyzers.cut_frequency import CutFrequencyAnalyzer
from app.core.analyzers.saliency import SaliencyAnalyzer

# 评估器
from app.core.evaluators.rule_evaluator import RuleEvaluator
from app.integrations import EvaluatorFactory


def convert_numpy_types(obj: Any) -> Any:
    """
    递归转换 numpy 类型为 Python 原生类型

    Args:
        obj: 可能包含 numpy 类型的对象

    Returns:
        转换后的 Python 原生类型对象
    """
    # 检查是否为 numpy 类型
    if isinstance(obj, np.generic):
        # 使用 item() 方法转换为 Python 原生类型
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class AnalysisService:
    """视频分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_video(
        self,
        video_id: str,
        use_ai: bool = True,
        api_key: str = None,
        ai_platform: str = None,
        ai_model: str = None,
        ai_base_url: str = None
    ) -> Dict[str, any]:
        """
        分析视频

        Args:
            video_id: 视频 ID
            use_ai: 是否使用 AI 评估
            api_key: API Key (可选，优先使用此 Key)
            ai_platform: AI 平台 (claude, aihubmix, openai 等，可选)
            ai_model: AI 模型名称 (可选)
            ai_base_url: API 基础 URL (可选，用于第三方平台)

        Returns:
            分析结果
        """
        try:
            logger.info(f"Starting analysis for video: {video_id}")

            # 1. 获取视频记录
            video = self.db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return {"success": False, "error": "视频不存在"}

            video_path = video.file_path
            duration = video.duration or 0

            # 2. 创建临时目录
            temp_dir = os.path.join(settings.TEMP_DIR, video_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 3. 特征提取
            logger.info(f"Extracting features for {video_id}")
            features = self._extract_features(video_path, temp_dir, duration)

            # 4. 运行分析器
            logger.info(f"Running analyzers for {video_id}")
            analysis_results = self._run_analyzers(features)

            # 5. 规则评分
            logger.info(f"Evaluating with rules for {video_id}")
            evaluation = self._evaluate_with_rules(analysis_results)

            # 6. AI 评估（可选）
            if use_ai:
                logger.info(f"Evaluating with AI for {video_id}")
                ai_result = self._evaluate_with_ai(
                    features,
                    evaluation,
                    api_key=api_key,
                    platform=ai_platform,
                    model=ai_model,
                    base_url=ai_base_url
                )
                evaluation["ai_evaluation"] = ai_result

            # 7. 保存结果
            logger.info(f"Saving results for {video_id}")
            result_id = self._save_results(video_id, evaluation)

            logger.info(f"Analysis completed for {video_id}")

            return {
                "success": True,
                "result_id": result_id,
                "evaluation": evaluation
            }

        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_features(
        self,
        video_path: str,
        temp_dir: str,
        duration: float
    ) -> Dict:
        """提取视频特征"""
        features = {}

        try:
            # 提取音频
            audio_path = os.path.join(temp_dir, "audio.wav")
            if not os.path.exists(audio_path):
                extract_audio(video_path, audio_path)
            features["audio_path"] = audio_path

            # 提取关键帧
            frames_dir = os.path.join(temp_dir, "frames")
            if not os.path.exists(frames_dir):
                os.makedirs(frames_dir)
                key_frames = extract_key_frames(video_path, frames_dir, fps=1)
            else:
                key_frames = sorted([
                    os.path.join(frames_dir, f)
                    for f in os.listdir(frames_dir)
                    if f.endswith('.jpg')
                ])
            features["key_frames"] = key_frames

            # ASR - 语音识别
            logger.info("Extracting audio text (ASR)")
            audio_extractor = get_audio_extractor(settings.WHISPER_MODEL)
            asr_result = audio_extractor.extract_text(audio_path)
            features["asr_text"] = asr_result["text"]
            features["asr_segments"] = asr_result["segments"]

            # OCR - 文字识别
            logger.info("Extracting text from frames (OCR)")
            text_extractor = get_text_extractor()
            ocr_text = text_extractor.get_all_text(key_frames, deduplicate=True)
            features["ocr_text"] = ocr_text

            # 场景检测
            logger.info("Detecting scenes")
            scene_extractor = get_scene_extractor()
            scenes = scene_extractor.detect_scenes(video_path)
            features["scenes"] = scenes

            # 视觉特征
            logger.info("Analyzing visual features")
            visual_extractor = get_visual_extractor()
            visual_features = visual_extractor.analyze_frames(key_frames)
            features["visual"] = visual_features

            logger.info("Feature extraction completed")
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return features

    def _run_analyzers(self, features: Dict) -> Dict:
        """运行所有分析器"""
        results = {}

        # 黄金3秒检测
        hook_detector = HookDetector()
        # 提取前3秒的文本
        first_3s_asr = self._get_text_in_range(
            features.get("asr_segments", []), 0, 3
        )
        first_3s_ocr = features.get("ocr_text", "")[:100]  # 简化：取前100字符
        saturation_change = features.get("visual", {}).get("avg_saturation", 0) / 100

        results["hook"] = hook_detector.analyze(
            first_3s_asr,
            first_3s_ocr,
            saturation_change
        )

        # CTA 检测
        cta_detector = CTADetector()
        # 提取最后5秒的文本
        duration = sum(end - start for start, end in features.get("scenes", []))
        last_5s_asr = self._get_text_in_range(
            features.get("asr_segments", []),
            max(0, duration - 5),
            duration
        )
        last_5s_ocr = features.get("ocr_text", "")[-100:]  # 简化：取后100字符

        results["cta"] = cta_detector.analyze(
            last_5s_asr,
            last_5s_ocr,
            duration
        )

        # 剪辑节奏分析
        cut_analyzer = CutFrequencyAnalyzer()
        results["cut_frequency"] = cut_analyzer.analyze(
            features.get("scenes", []),
            duration
        )

        # 视觉重心分析
        saliency_analyzer = SaliencyAnalyzer()
        visual_data = features.get("visual", {})
        results["saliency"] = saliency_analyzer.analyze(
            [visual_data.get("avg_product_area", 0.0)],
            [visual_data.get("avg_center_ratio", 0.0)],
            [visual_data.get("avg_blur_score", 100.0)]
        )

        return results

    def _evaluate_with_rules(self, analysis_results: Dict) -> Dict:
        """使用规则评分"""
        evaluator = RuleEvaluator()
        return evaluator.evaluate(
            analysis_results["hook"],
            analysis_results["cta"],
            analysis_results["cut_frequency"],
            analysis_results["saliency"]
        )

    def _evaluate_with_ai(
        self,
        features: Dict,
        evaluation: Dict,
        api_key: str = None,
        platform: str = None,
        model: str = None,
        base_url: str = None
    ) -> Dict:
        """使用 AI 评估

        Args:
            features: 特征数据
            evaluation: 规则评分结果
            api_key: API Key (可选)
            platform: AI 平台 (claude, aihubmix, openai 等)
            model: 模型名称 (可选)
            base_url: API 基础 URL (可选)
        """
        try:
            key_frames = features.get("key_frames", [])
            # 选择3个关键帧：开头、中间、结尾
            if len(key_frames) >= 3:
                selected_frames = [
                    key_frames[0],
                    key_frames[len(key_frames) // 2],
                    key_frames[-1]
                ]
            else:
                selected_frames = key_frames

            # 使用配置或默认值
            platform = platform or settings.AI_PLATFORM

            # 构建评估器参数
            evaluator_kwargs = {}

            # 根据平台设置默认参数
            if platform.lower() == "aihubmix":
                evaluator_kwargs["base_url"] = base_url or settings.AIHUBMIX_BASE_URL
                evaluator_kwargs["model"] = model or settings.AIHUBMIX_MODEL
            elif platform.lower() == "openai":
                evaluator_kwargs["base_url"] = base_url or settings.OPENAI_BASE_URL
                evaluator_kwargs["model"] = model or settings.OPENAI_MODEL
            elif platform.lower() == "claude":
                if model:
                    evaluator_kwargs["model"] = model

            # 创建评估器
            evaluator = EvaluatorFactory.create_evaluator(
                platform=platform,
                api_key=api_key,
                **evaluator_kwargs
            )

            logger.info(f"Using AI platform: {platform}")

            return evaluator.evaluate(
                selected_frames,
                features.get("asr_text", ""),
                features.get("ocr_text", ""),
                evaluation
            )
        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return {
                "summary": f"AI评估出错: {str(e)}",
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }

    def _save_results(self, video_id: str, evaluation: Dict) -> str:
        """保存分析结果"""
        result_id = f"res_{uuid.uuid4().hex[:12]}"

        # 转换 numpy 类型为 Python 原生类型
        evaluation_clean = convert_numpy_types(evaluation)

        result = AnalysisResult(
            id=result_id,
            video_id=video_id,
            overall_score=evaluation_clean["overall_score"],
            grade=evaluation_clean["grade"],
            structural_score=evaluation_clean["dimensions"]["structural"]["score"],
            visual_score=evaluation_clean["dimensions"]["visual"]["score"],
            structural_metrics=json.dumps(evaluation_clean["dimensions"]["structural"], ensure_ascii=False),
            visual_metrics=json.dumps(evaluation_clean["dimensions"]["visual"], ensure_ascii=False),
            issues=json.dumps(evaluation_clean["issues"], ensure_ascii=False),
            ai_evaluation=json.dumps(evaluation_clean.get("ai_evaluation", {}), ensure_ascii=False)
        )

        self.db.add(result)
        self.db.commit()

        return result_id

    def _get_text_in_range(
        self,
        segments: list,
        start_time: float,
        end_time: float
    ) -> str:
        """获取指定时间范围的文本"""
        texts = []
        for seg in segments:
            if seg["end"] >= start_time and seg["start"] <= end_time:
                texts.append(seg["text"])
        return " ".join(texts)

    def get_result(self, result_id: str) -> Dict:
        """获取分析结果"""
        result = self.db.query(AnalysisResult).filter(
            AnalysisResult.id == result_id
        ).first()

        if not result:
            return None

        return {
            "id": result.id,
            "video_id": result.video_id,
            "overall_score": result.overall_score,
            "grade": result.grade,
            "dimensions": {
                "structural": json.loads(result.structural_metrics),
                "visual": json.loads(result.visual_metrics)
            },
            "issues": json.loads(result.issues),
            "ai_evaluation": json.loads(result.ai_evaluation),
            "created_at": result.created_at.isoformat()
        }
