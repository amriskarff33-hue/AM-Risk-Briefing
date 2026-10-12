import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import api from './api'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import BriefDetail from './pages/BriefDetail'
import Channels from './pages/Channels'

function Protected({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState<boolean | null>(null)
  useEffect(() => {
    api.get('/auth/me').then(() => setAuthed(true)).catch(() => setAuthed(false))
  }, [])
  if (authed === null) return <div style={{ padding: 24 }}>Loading...</div>
  if (!authed) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/briefs/:id" element={<Protected><BriefDetail /></Protected>} />
      <Route path="/channels" element={<Protected><Channels /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
