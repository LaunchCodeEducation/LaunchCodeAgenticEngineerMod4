import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppDataProvider } from './context/AppDataContext'
import { FacebookConnectionProvider } from './context/FacebookConnectionContext'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { SearchWorkspacePage } from './pages/SearchWorkspacePage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <AppDataProvider>
        <FacebookConnectionProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="search/:id" element={<SearchWorkspacePage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="manage" element={<Navigate to="/" replace />} />
              <Route path="searches" element={<Navigate to="/" replace />} />
              <Route path="watchlist" element={<Navigate to="/" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </FacebookConnectionProvider>
      </AppDataProvider>
    </BrowserRouter>
  )
}

export default App
