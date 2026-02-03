import { Card, Typography } from 'antd'
import VideoUploader from '../../components/VideoUploader'

const { Title, Paragraph } = Typography

export default function UploadPage() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <Card bordered={false}>
        <Title level={2}>上传带货短视频</Title>
        <Paragraph style={{ color: '#666', marginBottom: '32px' }}>
          上传你的带货短视频，我们将自动分析视频的结构、视觉、音频等多个维度，
          并提供专业的评分和改进建议。
        </Paragraph>

        <VideoUploader />
      </Card>
    </div>
  )
}
