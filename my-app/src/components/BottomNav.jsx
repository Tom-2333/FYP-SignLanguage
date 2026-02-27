import React, { useState, useRef, useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { FaBookOpen, FaComments, FaHandsHelping, FaCog, FaBars, FaTimes, FaSignOutAlt } from 'react-icons/fa'
import { useLanguage } from '../contexts/LanguageContext'

export default function BottomNav() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)
  const btnRef = useRef(null)
  const navigate = useNavigate()
  const { t } = useLanguage()

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated')
    setOpen(false)
    navigate('/login')
  }

  // close when clicking outside
  useEffect(() => {
    function handleClick(e) {
      if (!containerRef.current) return
      if (
        containerRef.current.contains(e.target) ||
        (btnRef.current && btnRef.current.contains(e.target))
      ) {
        return
      }
      setOpen(false)
    }

    function handleEsc(e) {
      if (e.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', handleClick)
    document.addEventListener('touchstart', handleClick)
    document.addEventListener('keydown', handleEsc)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('touchstart', handleClick)
      document.removeEventListener('keydown', handleEsc)
    }
  }, [])

  const itemClass = ({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')

  return (
    <>
      {/* Toggle button in left-bottom corner */}
      <div className="floating-toggle">
        <button
          ref={btnRef}
          className="toggle-btn"
          onClick={() => setOpen((s) => !s)}
          aria-expanded={open}
          aria-controls="floating-nav"
          aria-label={open ? t('nav.closeMenu') : t('nav.openMenu')}
        >
          {open ? <FaTimes aria-hidden /> : <FaBars aria-hidden />}
        </button>

        {/* Floating nav panel */}
        <nav
          id="floating-nav"
          ref={containerRef}
          className={`floating-nav ${open ? 'open' : ''}`}
          role="navigation"
          aria-label="主要導航"
        >
          <NavLink to="/vocabulary" className={itemClass} onClick={() => setOpen(false)}>
            <FaBookOpen className="nav-icon" aria-hidden />
            <span className="nav-label">{t('nav.vocabulary')}</span>
          </NavLink>

          <NavLink to="/chat-box" className={itemClass} onClick={() => setOpen(false)}>
            <FaComments className="nav-icon" aria-hidden />
            <span className="nav-label">{t('nav.chatbox')}</span>
          </NavLink>

          <NavLink to="/support" className={itemClass} onClick={() => setOpen(false)}>
            <FaHandsHelping className="nav-icon" aria-hidden />
            <span className="nav-label">{t('nav.support')}</span>
          </NavLink>

          <NavLink to="/settings" className={itemClass} onClick={() => setOpen(false)}>
            <FaCog className="nav-icon" aria-hidden />
            <span className="nav-label">{t('nav.settings')}</span>
          </NavLink>

          <button className="nav-item logout-btn" onClick={handleLogout}>
            <FaSignOutAlt className="nav-icon" aria-hidden />
            <span className="nav-label">{t('nav.logout')}</span>
          </button>
        </nav>
      </div>

      {/* Backdrop to close when clicking outside (only when open) */}
      {open && <div className="floating-backdrop" onClick={() => setOpen(false)} aria-hidden="true" />}
    </>
  )
}