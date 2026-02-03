import { useState } from 'react'
import { Upload, message, Progress, Button } from 'antd'
import { InboxOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { uploadVideo, type VideoUploadResponse } from '../services/videoService'

const { Dragger } = Upload

interface VideoUploaderProps {
  onUploadSuccess?: (response: VideoUploadResponse) => void
}

export default function VideoUploader({ onUploadSuccess }: VideoUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null)

  const handleUpload = async (file: File) => {
    try {
      setUploading(true)
      setProgress(0)
      setUploadedVideo(null)

      const response = await uploadVideo(file, (progress) => {
        setProgress(progress)
      })

      setUploadedVideo(response)
      message.success('视频上传成功！')
      onUploadSuccess?.(response)
    } catch (error) {
      message.error(`上传失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setUploading(false)
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.mp4,.mov,.avi',
    beforeUpload: (file) => {
      // 验证文件类型
      const isVideo = file.type.startsWith('video/')
      if (!isVideo) {
        message.error('只能上传视频文件！')
        return Upload.LIST_IGNORE
      }

      // 验证文件大小（100MB）
      const isLt100M = file.size / 1024 / 1024 < 100
      if (!isLt100M) {
        message.error('视频大小不能超过 100MB！')
        return Upload.LIST_IGNORE
      }

      // 手动处理上传
      handleUpload(file)
      return false // 阻止自动上传
    },
    showUploadList: false,
  }

  return (
    <div>
      <Dragger {...uploadProps} disabled={uploading}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽视频文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 MP4、MOV、AVI 格式，文件大小不超过 100MB，时长 5-120 秒
        </p>
      </Dragger>

      {uploading && (
        <div style={{ marginTop: '20px' }}>
          <Progress percent={progress} status="active" />
          <p style={{ textAlign: 'center', marginTop: '10px', color: '#666' }}>
            正在上传视频...
          </p>
        </div>
      )}

      {uploadedVideo && !uploading && (
        <div
          style={{
            marginTop: '20px',
            padding: '20px',
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '24px', marginRight: '12px' }} />
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '16px' }}>上传成功</div>
              <div style={{ color: '#666', fontSize: '14px' }}>视频已保存，可以开始分析</div>
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <span style={{ color: '#666' }}>文件名：</span>
            <span style={{ fontWeight: 500 }}>{uploadedVideo.filename}</span>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <span style={{ color: '#666' }}>文件大小：</span>
            <span style={{ fontWeight: 500 }}>
              {(uploadedVideo.file_size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <span style={{ color: '#666' }}>视频 ID：</span>
            <span style={{ fontWeight: 500, fontFamily: 'monospace' }}>
              {uploadedVideo.video_id}
            </span>
          </div>

          <Button
            type="primary"
            size="large"
            block
            onClick={() => {
              // 这里稍后会跳转到分析页面
              window.location.href = `/analysis/${uploadedVideo.video_id}`
            }}
          >
            开始分析
          </Button>
        </div>
      )}
    </div>
  )
}
