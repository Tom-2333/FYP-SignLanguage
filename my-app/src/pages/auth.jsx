import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'
import './auth.css'

export default function Auth({ mode = 'login' }) {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const sldbApiBase = process.env.REACT_APP_SLDB_API_BASE || 'http://localhost/SL-Database_api'
  const [view, setView] = useState(mode) // 'login' or 'register'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!email || !password || (view === 'register' && !name)) {
      setError(t('auth.completeFields'))
      return
    }
    if (!email.includes('@')) {
      setError(t('auth.validEmail'))
      return
    }
    if (password.length < 6) {
      setError(t('auth.passwordLength'))
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${sldbApiBase}/login.php`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: view,
          email,
          username: name,
          password,
        }),
      })
      const data = await response.json()
      if (data.success) {
        if (view === 'register') {
          setView('login')
          setName('')
          setEmail('')
          setPassword('')
          // setError('Registration successful! Please log in.')
        } else {
          // Store user information in localStorage
          localStorage.setItem('isAuthenticated', 'true')
          localStorage.setItem('userName', data.username)
          localStorage.setItem('userId', data.user_id)
          localStorage.setItem('user', JSON.stringify({
            nickname: data.username,
            email: email,
            userId: data.user_id
          }))
          navigate('/vocabulary')
        }
      } else {
        setError(data.error || t('auth.authFailed'))
      }
    } catch (err) {
      setError(t('auth.networkError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h2>{view === 'login' ? t('auth.login') : t('auth.register')}</h2>

        <form onSubmit={submit} className="auth-form">
          {view === 'register' && (
            <label className="field">
              <div className="label">{t('auth.fullName')}</div>
              <input value={name} onChange={e => setName(e.target.value)} placeholder={t('auth.namePlaceholder')} />
            </label>
          )}

          <label className="field">
            <div className="label">{t('auth.email')}</div>
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder={t('auth.emailPlaceholder')} />
          </label>

          <label className="field">
            <div className="label">{t('auth.password')}</div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={t('auth.passwordPlaceholder')} />
          </label>

          {error && <div className="error">{error}</div>}

          <div className="actions">
            <button className="primary" type="submit" disabled={loading}>{loading ? t('auth.pleaseWait') : (view === 'login' ? t('auth.login') : t('auth.createAccount'))}</button>
          </div>
        </form>

        <div className="switch">
          {view === 'login' ? (
            <>
              <span>{t('auth.noAccount')}</span>
              <button className="link" onClick={() => setView('register')}>{t('auth.register')}</button>
            </>
          ) : (
            <>
              <span>{t('auth.hasAccount')}</span>
              <button className="link" onClick={() => setView('login')}>{t('auth.login')}</button>
            </>
          )}
        </div>

        <div className="alt-links">
          <Link to="/">{t('auth.backToApp')}</Link>
        </div>
      </div>
    </div>
  )
}
