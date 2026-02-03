import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Progress, Tag, Alert, Spin, Button, Divider } from 'antd'
import { startAnalysis, getResultByVideo, type AnalysisResult } from '../../services/analysisService'

export default function AnalysisPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (id) {
      loadAnalysisResult()
    }
  }, [id])

  const loadAnalysisResult = async () => {
    try {
      setLoading(true)
      setError('')

      // 尝试获取已有结果
      try {
        const data = await getResultByVideo(id!)
        setResult(data)
        setLoading(false)
        return
      } catch (err: any) {
        // 如果没有结果，开始分析
        if (err.response?.status === 404) {
          await performAnalysis()
        } else {
          throw err
        }
      }
    } catch (err: any) {
      setError(err.message || '加载失败')
      setLoading(false)
    }
  }

  const performAnalysis = async () => {
    try {
      setAnalyzing(true)

      // 开始分析
      const response = await startAnalysis(id!, true)

      // 获取结果
      const data = await getResultByVideo(id!)
      setResult(data)

    } catch (err: any) {
      setError(err.message || '分析失败')
    } finally {
      setAnalyzing(false)
      setLoading(false)
    }
  }

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return '#52c41a'
    if (grade.startsWith('B')) return '#1890ff'
    return '#faad14'
  }

  const getSeverityColor = (severity: string) => {
    if (severity === 'high') return 'error'
    if (severity === 'medium') return 'warning'
    return 'default'
  }

  if (loading || analyzing) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px', fontSize: '16px' }}>
          {analyzing ? '正在分析视频，请稍候...' : '加载中...'}
        </div>
        <div style={{ marginTop: '10px', color: '#666' }}>
          {analyzing && '这可能需要1-2分钟，请耐心等待'}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          action={
            <Button onClick={loadAnalysisResult}>重试</Button>
          }
        />
      </div>
    )
  }

  if (!result) {
    return <div>未找到分析结果</div>
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <Button
        onClick={() => navigate('/')}
        style={{ marginBottom: '16px' }}
      >
        ← 返回
      </Button>

      {/* 总分卡片 */}
      <Card style={{ marginBottom: '24px', textAlign: 'center' }}>
        <Row gutter={24} align="middle">
          <Col span={12}>
            <div style={{ fontSize: '72px', fontWeight: 'bold', color: getGradeColor(result.grade) }}>
              {result.overall_score.toFixed(1)}
            </div>
            <div style={{ fontSize: '24px', color: '#666', marginTop: '8px' }}>
              综合评分
            </div>
          </Col>
          <Col span={12}>
            <div style={{
              fontSize: '48px',
              fontWeight: 'bold',
              color: getGradeColor(result.grade)
            }}>
              {result.grade}
            </div>
            <div style={{ fontSize: '18px', color: '#666', marginTop: '8px' }}>
              质量等级
            </div>
          </Col>
        </Row>
      </Card>

      {/* 维度评分 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <Card title="🏆 结构化分析">
            <Progress
              type="circle"
              percent={result.dimensions.structural.score}
              format={(percent) => `${percent?.toFixed(1)}`}
              strokeColor={getGradeColor(result.grade)}
            />
            <Divider />
            <div>
              <div style={{ marginBottom: '12px' }}>
                <strong>黄金3秒:</strong> {result.dimensions.structural.hook.score}分
                {result.dimensions.structural.hook.detected && (
                  <Tag color="success" style={{ marginLeft: '8px' }}>检测到</Tag>
                )}
              </div>
              <div>
                <strong>CTA检测:</strong> {result.dimensions.structural.cta.score}分
                {result.dimensions.structural.cta.detected && (
                  <Tag color="success" style={{ marginLeft: '8px' }}>检测到</Tag>
                )}
              </div>
            </div>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="🎬 视觉动力学">
            <Progress
              type="circle"
              percent={result.dimensions.visual.score}
              format={(percent) => `${percent?.toFixed(1)}`}
              strokeColor={getGradeColor(result.grade)}
            />
            <Divider />
            <div>
              <div style={{ marginBottom: '12px' }}>
                <strong>剪辑节奏:</strong> {result.dimensions.visual.cut_frequency.score}分
                <div style={{ fontSize: '12px', color: '#666' }}>
                  平均镜头: {result.dimensions.visual.cut_frequency.avg_shot_length}秒
                </div>
              </div>
              <div>
                <strong>视觉重心:</strong> {result.dimensions.visual.saliency.score}分
                <div style={{ fontSize: '12px', color: '#666' }}>
                  产品占比: {(result.dimensions.visual.saliency.avg_product_area * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 问题列表 */}
      {result.issues && result.issues.length > 0 && (
        <Card
          title="⚠️ 需要改进的问题"
          style={{ marginBottom: '24px' }}
        >
          {result.issues.map((issue, index) => (
            <Alert
              key={index}
              message={issue.issue}
              type={getSeverityColor(issue.severity) as any}
              style={{ marginBottom: index < result.issues.length - 1 ? '12px' : 0 }}
            />
          ))}
        </Card>
      )}

      {/* AI 评估 */}
      {result.ai_evaluation && (
        <Card
          title="💡 AI 智能评估"
          style={{ marginBottom: '24px' }}
        >
          <div style={{ marginBottom: '24px' }}>
            <h4>综合评价</h4>
            <p style={{ fontSize: '16px', lineHeight: 1.6 }}>
              {result.ai_evaluation.summary}
            </p>
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <h4 style={{ color: '#52c41a' }}>✓ 优势</h4>
              <ul>
                {result.ai_evaluation.strengths?.map((strength, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>{strength}</li>
                ))}
              </ul>
            </Col>

            <Col span={12}>
              <h4 style={{ color: '#faad14' }}>⚠️ 劣势</h4>
              <ul>
                {result.ai_evaluation.weaknesses?.map((weakness, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>{weakness}</li>
                ))}
              </ul>
            </Col>
          </Row>

          <Divider />

          <h4>💡 改进建议</h4>
          <ul>
            {result.ai_evaluation.recommendations?.map((rec, index) => (
              <li key={index} style={{ marginBottom: '12px', fontSize: '15px' }}>
                {rec}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
