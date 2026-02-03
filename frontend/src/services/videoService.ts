import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export interface VideoUploadResponse {
  video_id: string
  filename: string
  file_path: string
  file_size: number
  status: string
  message: string
}

export interface VideoInfo {
  id: string
  filename: string
  file_path: string
  duration?: number
  resolution?: string
  fps?: number
  file_size: number
  status: string
  created_at: string
}

export interface VideoListResponse {
  total: number
  videos: VideoInfo[]
}

/**
 * 上传视频
 */
export const uploadVideo = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<VideoUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<VideoUploadResponse>(
    `${API_BASE_URL}/videos/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5分钟
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress?.(progress)
        }
      },
    }
  )

  return response.data
}

/**
 * 获取视频信息
 */
export const getVideo = async (videoId: string): Promise<VideoInfo> => {
  const response = await axios.get<VideoInfo>(
    `${API_BASE_URL}/videos/${videoId}`
  )
  return response.data
}

/**
 * 获取视频列表
 */
export const getVideoList = async (
  skip: number = 0,
  limit: number = 20
): Promise<VideoListResponse> => {
  const response = await axios.get<VideoListResponse>(
    `${API_BASE_URL}/videos`,
    {
      params: { skip, limit },
    }
  )
  return response.data
}

/**
 * 删除视频
 */
export const deleteVideo = async (videoId: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/videos/${videoId}`)
}
