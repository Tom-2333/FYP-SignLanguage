import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Vocabulary from './pages/vocabulary.jsx'
import ChatBox from './pages/chatBox.jsx'
import Auth from './pages/auth.jsx'
import Support from './pages/support.jsx'
import Settings from './pages/settings.jsx'
import BottomNav from './components/BottomNav.jsx'
import { LanguageProvider } from './contexts/LanguageContext'

// Protected Route Component
function ProtectedRoute({ children }) {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <div className="app">
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Navigate to="/vocabulary" replace />} />
              <Route path="/vocabulary" element={<ProtectedRoute><Vocabulary /></ProtectedRoute>} />
              <Route path="/chat-box" element={<ProtectedRoute><ChatBox /></ProtectedRoute>} />
              <Route path="/support" element={<ProtectedRoute><Support /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
              <Route path="/login" element={<Auth mode="login" />} />
              <Route path="/register" element={<Auth mode="register" />} />
            </Routes>
          </div>

          {/* Bottom navigation is outside Routes so it shows on every page */}
          <BottomNav />
        </div>
      </BrowserRouter>
    </LanguageProvider>
  )
}