import React, { useState, useEffect } from 'react'
import { FaUser, FaEnvelope, FaPalette, FaSignOutAlt, FaMoon, FaSun } from 'react-icons/fa'
import './settings.css'

export default function Settings() {
  const [userInfo, setUserInfo] = useState({
    nickname: '',
    email: ''
  })
  const [colorMode, setColorMode] = useState('light')
  const [rgCvdMode, setRgCvdMode] = useState(false)
  const [fontSize, setFontSize] = useState('100%')
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    // Load user info from localStorage or context
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      const userData = JSON.parse(storedUser)
      setUserInfo({
        nickname: userData.nickname || userData.username || 'User',
        email: userData.email || 'user@example.com'
      })
    }

    // Load color mode preference
    const savedColorMode = localStorage.getItem('colorMode') || 'light'
    setColorMode(savedColorMode)
    applyColorMode(savedColorMode)

    // Load RG-CVD mode preference
    const savedRgCvdMode = localStorage.getItem('rgCvdMode') === 'true'
    setRgCvdMode(savedRgCvdMode)
    applyRgCvdMode(savedRgCvdMode)

    // Load font size preference
    const savedFontSize = localStorage.getItem('fontSize') || '100%'
    setFontSize(savedFontSize)
  }, [])

  const applyColorMode = (mode) => {
    if (mode === 'dark') {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }

  const applyRgCvdMode = (enabled) => {
    if (enabled) {
      document.body.classList.add('rg-cvd-mode')
    } else {
      document.body.classList.remove('rg-cvd-mode')
    }
  }

  const handleColorModeChange = (mode) => {
    setColorMode(mode)
    setHasChanges(true)
  }

  const handleRgCvdModeChange = (enabled) => {
    setRgCvdMode(enabled)
    setHasChanges(true)
  }

  const handleFontSizeChange = (size) => {
    setFontSize(size)
    setHasChanges(true)
  }

  const handleSaveSettings = () => {
    // Save color mode
    localStorage.setItem('colorMode', colorMode)
    applyColorMode(colorMode)

    // Save RG-CVD mode
    localStorage.setItem('rgCvdMode', rgCvdMode.toString())
    applyRgCvdMode(rgCvdMode)

    // Save font size
    localStorage.setItem('fontSize', fontSize)

    setHasChanges(false)
  }

  const handleLogout = () => {
    // Clear user data from localStorage
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    
    // Redirect to login page or auth page
    window.location.href = '/auth'
  }

  return (
    <div className="settings-container">
      <div className="settings-wrapper">
        <header className="settings-header">
          <h1>Settings</h1>
          <p>Manage your account preferences</p>
        </header>

        <div className="settings-content">
          {/* User Information Section */}
          <section className="settings-section">
            <h2 className="section-title">Account Information</h2>
            
            <div className="info-card">
              <div className="info-row">
                <div className="info-icon">
                  <FaUser />
                </div>
                <div className="info-details">
                  <label>Nickname</label>
                  <p>{userInfo.nickname}</p>
                </div>
              </div>
            </div>

            <div className="info-card">
              <div className="info-row">
                <div className="info-icon">
                  <FaEnvelope />
                </div>
                <div className="info-details">
                  <label>Email</label>
                  <p>{userInfo.email}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Appearance Section */}
          <section className="settings-section">
            <h2 className="section-title">Appearance</h2>
            
            <div className="info-card">
              <div className="info-row">
                <div className="info-icon">
                  <FaPalette />
                </div>
                <div className="info-details">
                  <label>Color Mode</label>
                  <div className="color-mode-toggle">
                    <button
                      className={`mode-btn ${colorMode === 'light' ? 'active' : ''}`}
                      onClick={() => handleColorModeChange('light')}
                    >
                      <FaSun /> Light
                    </button>
                    <button
                      className={`mode-btn ${colorMode === 'dark' ? 'active' : ''}`}
                      onClick={() => handleColorModeChange('dark')}
                    >
                      <FaMoon /> Dark
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Font Size Section */}
          <section className="settings-section">
            <h2 className="section-title">Font Size</h2>
            
            <div className="info-card">
              <div className="info-row">
                <div className="info-details">
                  <label>Text Size</label>
                  <div className="font-size-controls">
                    <button
                      type="button"
                      className={`font-size-btn size-small ${fontSize === '90%' ? 'active' : ''}`}
                      onClick={() => handleFontSizeChange('90%')}
                      title="Small (90%)"
                    >
                      aa
                    </button>
                    <button
                      type="button"
                      className={`font-size-btn size-normal ${fontSize === '100%' ? 'active' : ''}`}
                      onClick={() => handleFontSizeChange('100%')}
                      title="Normal (100%)"
                    >
                      Aa
                    </button>
                    <button
                      type="button"
                      className={`font-size-btn size-large ${fontSize === '125%' ? 'active' : ''}`}
                      onClick={() => handleFontSizeChange('125%')}
                      title="Large (125%)"
                    >
                      AA
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Accessibility Section */}
          <section className="settings-section">
            <h2 className="section-title">Accessibility</h2>
            
            <div className="info-card">
              <div className="accessibility-options">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={rgCvdMode}
                    onChange={(e) => handleRgCvdModeChange(e.target.checked)}
                    className="accessibility-checkbox"
                  />
                  <span className="checkbox-text">
                    <strong>Color Blind Friendly Mode (RG-CVD)</strong>
                    <small>Optimized colors for red-green color vision deficiency</small>
                  </span>
                </label>
              </div>
            </div>
          </section>

          {/* Save Button */}
          {hasChanges && (
            <div className="save-section">
              <button className="save-btn" onClick={handleSaveSettings}>
                Save Settings
              </button>
            </div>
          )}
        </div>

        {/* Logout Button */}
        <div className="settings-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <FaSignOutAlt /> Logout
          </button>
        </div>
      </div>
    </div>
  )
}
