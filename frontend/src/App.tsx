import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Layout, Menu, Button } from 'antd'
import { UploadOutlined, BarChartOutlined, HistoryOutlined, SettingOutlined } from '@ant-design/icons'
import { useState } from 'react'
import UploadPage from './pages/Upload'
import AnalysisPage from './pages/Analysis'
import HistoryPage from './pages/History'
import SettingsModal from './components/SettingsModal'

const { Header, Content } = Layout

function App() {
  const [settingsVisible, setSettingsVisible] = useState(false)

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', marginRight: '40px' }}>
            带货视频质量评估系统
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['upload']}
            style={{ flex: 1, minWidth: 0 }}
            items={[
              { key: 'upload', icon: <UploadOutlined />, label: <Link to="/">上传视频</Link> },
              { key: 'history', icon: <HistoryOutlined />, label: <Link to="/history">历史记录</Link> }
            ]}
          />
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setSettingsVisible(true)}
            style={{ color: 'white' }}
          >
            设置
          </Button>
        </Header>
        <Content style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/analysis/:id" element={<AnalysisPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </Content>
      </Layout>
      <SettingsModal
        visible={settingsVisible}
        onClose={() => setSettingsVisible(false)}
      />
    </Router>
  )
}

export default App
