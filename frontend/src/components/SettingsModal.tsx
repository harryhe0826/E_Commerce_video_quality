import { useState, useEffect } from 'react'
import { Modal, Input, Button, Alert, Space, Select, Divider, message, AutoComplete } from 'antd'
import { SettingOutlined, KeyOutlined, CloudOutlined, ApiOutlined, ReloadOutlined } from '@ant-design/icons'

const { Option } = Select

interface SettingsModalProps {
  visible: boolean
  onClose: () => void
}

interface AISettings {
  platform: 'claude' | 'aihubmix' | 'openai'
  apiKey: string
  model?: string
  baseUrl?: string
}

const DEFAULT_SETTINGS: AISettings = {
  platform: 'claude',
  apiKey: '',
  model: '',
  baseUrl: ''
}

const PLATFORM_INFO = {
  claude: {
    name: 'Claude (Anthropic)',
    defaultModel: 'claude-3-5-sonnet-20241022',
    models: [
      'claude-3-5-sonnet-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229'
    ],
    placeholder: 'sk-ant-api03-xxxxxxxxxxxxx',
    docs: 'https://console.anthropic.com/',
    description: '官方 Claude API，高质量输出，适合对质量要求高的场景',
    requiresBaseUrl: false
  },
  aihubmix: {
    name: 'Aihubmix（第三方聚合平台）',
    defaultModel: 'glm-4.6v',
    defaultBaseUrl: 'https://aihubmix.com/v1',
    models: [],  // 动态获取
    placeholder: 'your_aihubmix_api_key',
    docs: 'https://aihubmix.com',
    description: '支持多种模型，价格灵活，适合需要切换不同模型的场景',
    requiresBaseUrl: true,
    supportsDynamicModels: true
  },
  openai: {
    name: 'OpenAI',
    defaultModel: 'glm-4.6v',
    defaultBaseUrl: 'https://api.openai.com/v1',
    models: [],  // 动态获取
    placeholder: 'sk-xxxxxxxxxxxxx',
    docs: 'https://platform.openai.com',
    description: '官方 OpenAI API，响应速度快，性价比高',
    requiresBaseUrl: false,
    supportsDynamicModels: true
  }
}

export default function SettingsModal({ visible, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState<AISettings>(DEFAULT_SETTINGS)
  const [savedSettings, setSavedSettings] = useState<AISettings | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [loadingModels, setLoadingModels] = useState(false)

  useEffect(() => {
    // 加载已保存的设置
    const saved = localStorage.getItem('ai_settings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setSavedSettings(parsed)
        setSettings(parsed)
      } catch (e) {
        console.error('Failed to parse saved settings:', e)
      }
    } else {
      // 兼容旧版本：检查是否有 claude_api_key
      const oldKey = localStorage.getItem('claude_api_key')
      if (oldKey) {
        const migratedSettings = {
          platform: 'claude' as const,
          apiKey: oldKey,
          model: PLATFORM_INFO.claude.defaultModel
        }
        setSettings(migratedSettings)
        setSavedSettings(migratedSettings)
      }
    }
  }, [visible])

  const handleSave = () => {
    if (!settings.apiKey.trim()) {
      Modal.warning({
        title: '提示',
        content: '请输入 API Key'
      })
      return
    }

    // 确保必填字段
    const settingsToSave = {
      ...settings,
      apiKey: settings.apiKey.trim(),
      model: settings.model || PLATFORM_INFO[settings.platform].defaultModel,
      baseUrl: PLATFORM_INFO[settings.platform].requiresBaseUrl
        ? settings.baseUrl || PLATFORM_INFO[settings.platform].defaultBaseUrl
        : undefined
    }

    localStorage.setItem('ai_settings', JSON.stringify(settingsToSave))
    setSavedSettings(settingsToSave)

    Modal.success({
      title: '保存成功',
      content: `${PLATFORM_INFO[settings.platform].name} 配置已保存`
    })
    onClose()
  }

  const handleClear = () => {
    Modal.confirm({
      title: '确认清除',
      content: '确定要清除所有已保存的设置吗？',
      onOk: () => {
        localStorage.removeItem('ai_settings')
        // 清除旧版本的 key（兼容性）
        localStorage.removeItem('claude_api_key')
        setSettings(DEFAULT_SETTINGS)
        setSavedSettings(null)
      }
    })
  }

  const handlePlatformChange = (platform: 'claude' | 'aihubmix' | 'openai') => {
    setSettings({
      platform,
      apiKey: settings.apiKey,
      model: PLATFORM_INFO[platform].defaultModel,
      baseUrl: PLATFORM_INFO[platform].defaultBaseUrl || ''
    })
  }

  const maskKey = (key: string) => {
    if (!key) return ''
    if (key.length <= 20) return key
    return key.substring(0, 10) + '...' + key.substring(key.length - 10)
  }

  const fetchModels = async () => {
    const currentPlatform = PLATFORM_INFO[settings.platform]

    // 如果不支持动态获取，直接返回
    if (!currentPlatform.supportsDynamicModels) {
      return
    }

    if (!settings.apiKey.trim()) {
      message.warning('请先输入 API Key')
      return
    }

    const baseUrl = currentPlatform.requiresBaseUrl
      ? (settings.baseUrl || currentPlatform.defaultBaseUrl)
      : currentPlatform.defaultBaseUrl

    if (!baseUrl) {
      message.warning('请先输入 Base URL')
      return
    }

    setLoadingModels(true)
    try {
      const response = await fetch(`${baseUrl}/models`, {
        headers: {
          'Authorization': `Bearer ${settings.apiKey}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      // OpenAI API 格式: { data: [{id: "model-name"}, ...] }
      if (data.data && Array.isArray(data.data)) {
        const models = data.data
          .map((m: any) => m.id || m.name)
          .filter((id: string) => id)
        setAvailableModels(models)
        message.success(`成功获取 ${models.length} 个可用模型`)
      } else if (Array.isArray(data)) {
        // 直接返回数组格式
        const models = data.map((m: any) => typeof m === 'string' ? m : (m.id || m.name)).filter(Boolean)
        setAvailableModels(models)
        message.success(`成功获取 ${models.length} 个可用模型`)
      } else {
        throw new Error('Unexpected API response format')
      }
    } catch (error) {
      console.error('Failed to fetch models:', error)
      message.error(`获取模型列表失败: ${error instanceof Error ? error.message : '未知错误'}`)
      // 失败时使用默认模型
      setAvailableModels([currentPlatform.defaultModel])
    } finally {
      setLoadingModels(false)
    }
  }

  const currentPlatform = PLATFORM_INFO[settings.platform]

  return (
    <Modal
      title={
        <Space>
          <SettingOutlined />
          <span>AI 平台设置</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="clear" onClick={handleClear} disabled={!savedSettings} danger>
          清除所有设置
        </Button>,
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="save" type="primary" onClick={handleSave}>
          保存
        </Button>
      ]}
      width={700}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 平台选择 */}
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>
            <CloudOutlined /> 选择 AI 平台
          </div>
          <Select
            value={settings.platform}
            onChange={handlePlatformChange}
            style={{ width: '100%' }}
            size="large"
          >
            <Option value="claude">{PLATFORM_INFO.claude.name}</Option>
            <Option value="aihubmix">{PLATFORM_INFO.aihubmix.name}</Option>
            <Option value="openai">{PLATFORM_INFO.openai.name}</Option>
          </Select>
          <Alert
            message={currentPlatform.description}
            type="info"
            showIcon
            style={{ marginTop: 8 }}
          />
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* API Key */}
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>
            <KeyOutlined /> API Key
          </div>
          <Input.Password
            placeholder={currentPlatform.placeholder}
            value={settings.apiKey}
            onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
            style={{ marginBottom: 8 }}
            size="large"
          />
          {savedSettings?.platform === settings.platform && savedSettings?.apiKey && (
            <div style={{ fontSize: 12, color: '#52c41a' }}>
              ✓ 已保存: {maskKey(savedSettings.apiKey)}
            </div>
          )}
          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
            <a href={currentPlatform.docs} target="_blank" rel="noopener noreferrer">
              → 前往 {currentPlatform.name} 获取 API Key
            </a>
          </div>
        </div>

        {/* 模型选择 */}
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              <ApiOutlined /> 模型选择
            </span>
            {currentPlatform.supportsDynamicModels && (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={fetchModels}
                loading={loadingModels}
                disabled={!settings.apiKey.trim()}
              >
                刷新模型列表
              </Button>
            )}
          </div>
          {currentPlatform.supportsDynamicModels ? (
            <AutoComplete
              value={settings.model || currentPlatform.defaultModel}
              onChange={(model) => setSettings({ ...settings, model })}
              options={
                availableModels.length > 0
                  ? availableModels.map((model) => ({ value: model, label: model }))
                  : [{ value: currentPlatform.defaultModel, label: `${currentPlatform.defaultModel} (默认)` }]
              }
              placeholder="输入或选择模型名称"
              style={{ width: '100%' }}
              size="large"
              filterOption={(inputValue, option) =>
                option?.value.toLowerCase().includes(inputValue.toLowerCase()) ?? false
              }
            />
          ) : (
            <Select
              value={settings.model || currentPlatform.defaultModel}
              onChange={(model) => setSettings({ ...settings, model })}
              style={{ width: '100%' }}
              size="large"
            >
              {currentPlatform.models.map((model) => (
                <Option key={model} value={model}>
                  {model}
                </Option>
              ))}
            </Select>
          )}
          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
            {currentPlatform.supportsDynamicModels ? (
              <>可手动输入模型名称，或点击"刷新模型列表"获取可用模型</>
            ) : (
              <>默认模型: {currentPlatform.defaultModel}</>
            )}
          </div>
        </div>

        {/* Base URL (仅对需要的平台显示) */}
        {currentPlatform.requiresBaseUrl && (
          <div>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              <ApiOutlined /> API Base URL
            </div>
            <Input
              placeholder={currentPlatform.defaultBaseUrl}
              value={settings.baseUrl || currentPlatform.defaultBaseUrl}
              onChange={(e) => setSettings({ ...settings, baseUrl: e.target.value })}
              size="large"
            />
            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
              默认: {currentPlatform.defaultBaseUrl}
            </div>
          </div>
        )}

        <Divider style={{ margin: '12px 0' }} />

        {/* 使用说明 */}
        <Alert
          message="使用说明"
          description={
            <div>
              <p style={{ marginBottom: 8 }}>
                <strong>支持的平台：</strong>
              </p>
              <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                <li><strong>Claude:</strong> 高质量 AI 评估，适合专业分析</li>
                <li><strong>Aihubmix:</strong> 第三方聚合平台，支持多种模型切换，可动态获取模型列表</li>
                <li><strong>OpenAI:</strong> GPT 系列模型，响应快速，支持动态获取模型列表</li>
              </ul>
              <p style={{ marginBottom: 8 }}>
                <strong>模型选择：</strong>对于第三方平台，可以手动输入模型名称（如 glm-4.6v），或点击"刷新模型列表"按钮获取所有可用模型。
              </p>
              <p style={{ marginBottom: 0 }}>
                <strong>隐私保护：</strong>所有配置仅保存在浏览器本地，不会上传到服务器。
              </p>
            </div>
          }
          type="success"
          showIcon
        />
      </Space>
    </Modal>
  )
}
