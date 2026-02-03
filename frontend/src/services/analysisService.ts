import axios from 'axios'

// 使用环境变量，开发环境默认使用 localhost
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : 'http://localhost:8000/api'

export interface AnalysisResult {
  id: string
  video_id: string
  overall_score: number
  grade: string
  dimensions: {
    structural: {
      score: number
      hook: any
      cta: any
    }
    visual: {
      score: number
      cut_frequency: any
      saliency: any
    }
  }
  issues: any[]
  ai_evaluation: {
    summary: string
    strengths: string[]
    weaknesses: string[]
    recommendations: string[]
  }
  created_at: string
}

interface AISettings {
  platform: 'claude' | 'aihubmix' | 'openai'
  apiKey: string
  model?: string
  baseUrl?: string
}

/**
 * 从 localStorage 获取 AI 设置
 */
const getAISettings = (): AISettings | null => {
  // 先尝试新格式
  const newSettings = localStorage.getItem('ai_settings')
  if (newSettings) {
    try {
      return JSON.parse(newSettings)
    } catch (e) {
      console.error('Failed to parse AI settings:', e)
    }
  }

  // 兼容旧格式（只有 Claude API Key）
  const oldKey = localStorage.getItem('claude_api_key')
  if (oldKey) {
    return {
      platform: 'claude',
      apiKey: oldKey,
      model: 'claude-3-5-sonnet-20241022'
    }
  }

  return null
}

/**
 * 开始分析视频
 */
export const startAnalysis = async (
  videoId: string,
  useAI: boolean = true
): Promise<{ result_id: string; status: string }> => {
  const settings = getAISettings()

  const headers: any = {}

  if (settings && settings.apiKey) {
    // 使用新的通用 headers
    headers['x-ai-platform'] = settings.platform
    headers['x-ai-api-key'] = settings.apiKey

    if (settings.model) {
      headers['x-ai-model'] = settings.model
    }

    if (settings.baseUrl) {
      headers['x-ai-base-url'] = settings.baseUrl
    }

    // 为了向后兼容，如果是 Claude 平台，也设置旧的 header
    if (settings.platform === 'claude') {
      headers['X-Claude-API-Key'] = settings.apiKey
    }
  }

  const response = await axios.post(
    `${API_BASE_URL}/analysis/start/${videoId}`,
    null,
    {
      params: { use_ai: useAI },
      headers,
      timeout: 600000 // 10分钟超时（视频分析可能很耗时）
    }
  )
  return response.data
}

/**
 * 获取分析结果
 */
export const getAnalysisResult = async (
  resultId: string
): Promise<AnalysisResult> => {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/result/${resultId}`
  )
  return response.data
}

/**
 * 根据视频ID获取分析结果
 */
export const getResultByVideo = async (
  videoId: string
): Promise<AnalysisResult> => {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/result/by-video/${videoId}`
  )
  return response.data
}

/**
 * 获取分析结果列表
 */
export const getAnalysisList = async (
  skip: number = 0,
  limit: number = 20
): Promise<{ total: number; results: any[] }> => {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/list`,
    {
      params: { skip, limit }
    }
  )
  return response.data
}
