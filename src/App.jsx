import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Vocabulary from './pages/vocabulary'
import ChatBox from './pages/chatBox'
import Auth from './pages/auth'
import BottomNav from './components/BottomNav'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Navigate to="/vocabulary" replace />} />
            <Route path="/vocabulary" element={<Vocabulary />} />
            <Route path="/chat-box" element={<ChatBox />} />
            <Route path="/login" element={<Auth mode="login" />} />
            <Route path="/register" element={<Auth mode="register" />} />
          </Routes>
        </div>

        {/* Bottom navigation is outside Routes so it shows on every page */}
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}